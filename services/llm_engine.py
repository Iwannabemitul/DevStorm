"""
LLMEngine: a singleton, provider-agnostic router.
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

GEMINI_MODEL_PRIORITY: List[str] = [
    "models/gemini-2.0-flash",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
    "models/gemini-pro",
]

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Ordered priority list for NVIDIA NIM models
NVIDIA_CANDIDATE_MODELS: List[str] = [
    "google/diffusiongemma-26b-a4b-it",
    "moonshotai/kimi-k3",
    "meta/llama-3.3-70b-instruct",
    "mistralai/mistral-nemo-12b-instruct",
]


class LLMEngineError(RuntimeError):
    """Raised whenever no provider could produce a usable, schema-valid response."""


class LLMEngine:
    """Process-wide singleton. Safe to call `LLMEngine.get_instance()` anywhere."""

    _instance: Optional["LLMEngine"] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
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

    def configure(self, gemini_api_key: Optional[str], nvidia_api_key: Optional[str]) -> None:
        self._gemini_api_key = gemini_api_key or None
        self._nvidia_api_key = nvidia_api_key or None

    def is_configured(self) -> bool:
        return bool(self._gemini_api_key) or bool(self._nvidia_api_key)

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
        errors = []

        for model_name in NVIDIA_CANDIDATE_MODELS:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a senior technical evaluator. You must return only valid, "
                                "well-formed JSON with no extra conversational text or markdown explanation."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=4096,
                    temperature=0.2,
                )

                if not completion.choices:
                    continue

                msg = completion.choices[0].message
                # Check message content, fallback to reasoning_content if content is empty
                text = (msg.content or "").strip()
                if not text and hasattr(msg, "reasoning_content") and msg.reasoning_content:
                    text = msg.reasoning_content.strip()

                if text:
                    return text

            except Exception as exc:
                errors.append(f"{model_name}: {exc}")
                continue

        raise RuntimeError(f"NVIDIA candidates failed or returned empty: {' | '.join(errors)}")

    def generate_text(self, prompt: str) -> str:
        """Resilient router: try Gemini, then fall back to NVIDIA NIM models."""
        errors: List[str] = []

        with self._call_lock:
            if self._gemini_api_key:
                try:
                    return self._call_gemini(prompt)
                except Exception as exc:
                    errors.append(f"Gemini Error: {exc}")

            if self._nvidia_api_key:
                try:
                    return self._call_nvidia(prompt)
                except Exception as exc:
                    errors.append(f"NVIDIA Error: {exc}")

        if errors:
            raise LLMEngineError(" | ".join(errors))
        raise LLMEngineError("No LLM provider is configured.")

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
            raise LLMEngineError(f"No JSON object found in LLM response: {text[:150]}...")
        return text[start : end + 1]

    @staticmethod
    def _repair_common_json_issues(json_str: str) -> str:
        json_str = json_str.replace("\u201c", '"').replace("\u201d", '"')
        json_str = json_str.replace("\u2018", "'").replace("\u2019", "'")
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
        json_str = json_str.replace("\r", " ")
        return json_str

    @classmethod
    def extract_json(cls, raw_text: str) -> Dict[str, Any]:
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

    def generate_structured(self, prompt: str, schema: Type[SchemaT]) -> SchemaT:
        raw_text = self.generate_text(prompt)
        data = self.extract_json(raw_text)
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise LLMEngineError(f"LLM output failed schema validation: {exc}") from exc