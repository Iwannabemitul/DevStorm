"""
LLMEngine: a singleton, provider-agnostic router.

Round 1 had the Gemini multi-model-discovery + NVIDIA Llama-3.3 fallback
logic, JSON string-slicing, and prompt construction all inline inside
app.py. This module encapsulates the "call some LLM and get back a
validated object" concern so nothing above this layer needs to know which
provider answered, or care about code fences / stray commas in the raw
text.

Usage:
    engine = LLMEngine.get_instance()
    engine.configure(gemini_api_key=..., nvidia_api_key=...)
    result: AnalysisResult = engine.generate_structured(prompt, AnalysisResult)
"""
from __future__ import annotations

import json
import re
import threading
from typing import Any, Dict, List, Optional, Type, TypeVar

import google.generativeai as genai
from openai import OpenAI
from pydantic import BaseModel, ValidationError

SchemaT = TypeVar("SchemaT", bound=BaseModel)

# Preference order when multiple Gemini models are available to the key.
GEMINI_MODEL_PRIORITY: List[str] = [
    "models/gemini-3.6-flash",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
    "models/gemini-2.0-flash",
    "models/gemini-pro",
]

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.3-70b-instruct-v2"


class LLMEngineError(RuntimeError):
    """Raised whenever no provider could produce a usable, schema-valid response."""


class LLMEngine:
    """Process-wide singleton. Safe to call `LLMEngine.get_instance()` anywhere."""

    _instance: Optional["LLMEngine"] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        # Guard against accidental direct instantiation creating a second
        # "singleton" -- always go through get_instance().
        self._gemini_api_key: Optional[str] = None
        self._nvidia_api_key: Optional[str] = None
        self._call_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "LLMEngine":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, gemini_api_key: Optional[str], nvidia_api_key: Optional[str]) -> None:
        """(Re)inject provider keys. Safe to call every Streamlit rerun -- it's just
        an attribute swap, not a network call."""
        self._gemini_api_key = gemini_api_key or None
        self._nvidia_api_key = nvidia_api_key or None

    def is_configured(self) -> bool:
        return bool(self._gemini_api_key) or bool(self._nvidia_api_key)

    # ------------------------------------------------------------------
    # Provider calls
    # ------------------------------------------------------------------

    def _call_gemini(self, prompt: str) -> str:
        genai.configure(api_key=self._gemini_api_key)
        available_models = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]

        selected_model_name = next(
            (candidate for candidate in GEMINI_MODEL_PRIORITY if candidate in available_models),
            None,
        )
        if selected_model_name is None and available_models:
            selected_model_name = available_models[0]
        if selected_model_name is None:
            raise RuntimeError("No Gemini models supporting generateContent are available.")

        model = genai.GenerativeModel(selected_model_name)
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text

    def _call_nvidia(self, prompt: str) -> str:
        client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=self._nvidia_api_key)
        completion = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.2,
        )
        text = (completion.choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("NVIDIA returned an empty response.")
        return text

    def generate_text(self, prompt: str) -> str:
        """Resilient router: try Gemini, then fall back to the NVIDIA Llama-3.3 endpoint."""
        errors: List[str] = []

        with self._call_lock:
            if self._gemini_api_key:
                try:
                    return self._call_gemini(prompt)
                except Exception as exc:  # noqa: BLE001 - deliberately broad, this is a fallback boundary
                    errors.append(f"Gemini Error: {exc}")

            if self._nvidia_api_key:
                try:
                    return self._call_nvidia(prompt)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"NVIDIA Error: {exc}")

        if errors:
            raise LLMEngineError(" | ".join(errors))
        raise LLMEngineError("No LLM provider is configured.")

    # ------------------------------------------------------------------
    # JSON extraction + auto-repair
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        return text

    @staticmethod
    def _isolate_json_object(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise LLMEngineError("No JSON object found in the LLM response.")
        return text[start:end + 1]

    @staticmethod
    def _repair_common_json_issues(json_str: str) -> str:
        """Best-effort fixes for the mistakes small/medium LLMs make most often.

        This is intentionally a heuristic pass, not a full JSON5 parser -- it
        targets the failure modes actually seen from these prompts:
        trailing commas, smart quotes, and stray control characters.
        """
        # Smart/curly quotes -> straight quotes.
        json_str = json_str.replace("\u201c", '"').replace("\u201d", '"')
        json_str = json_str.replace("\u2018", "'").replace("\u2019", "'")
        # Trailing commas before a closing brace/bracket.
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
        # Raw newlines/tabs inside the object (outside of what json expects).
        json_str = json_str.replace("\r", " ")
        return json_str

    @classmethod
    def extract_json(cls, raw_text: str) -> Dict[str, Any]:
        """Strip code fences, isolate the JSON object, and parse it -- repairing
        common formatting mistakes if the first parse attempt fails."""
        if not raw_text:
            raise LLMEngineError("Empty response from LLM provider.")

        text = cls._strip_code_fences(raw_text)
        json_slice = cls._isolate_json_object(text)

        try:
            return json.loads(json_slice)
        except json.JSONDecodeError:
            repaired = cls._repair_common_json_issues(json_slice)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as exc:
                raise LLMEngineError(f"Failed to parse JSON from LLM response: {exc}") from exc

    # ------------------------------------------------------------------
    # High-level structured entry point
    # ------------------------------------------------------------------

    def generate_structured(self, prompt: str, schema: Type[SchemaT]) -> SchemaT:
        """Call the resilient router, extract/repair JSON, then validate against
        `schema`. Raises LLMEngineError on any failure in the chain -- callers
        should catch this once and decide on a fallback (e.g. the legacy
        keyword-matching analyzer)."""
        raw_text = self.generate_text(prompt)
        data = self.extract_json(raw_text)
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise LLMEngineError(f"LLM output failed schema validation: {exc}") from exc
