"""
Pydantic schemas shared across the service layer.

Every value that comes back from an LLM call or a third-party API gets
validated against one of these models before it is trusted by the rest of
the app. This is the enforcement point requested for Round 2: no raw
`dict`s from `json.loads` cross a service boundary.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------
# Skill-gap analysis
# --------------------------------------------------------------------------

class AnalysisResult(BaseModel):
    """Normalized output of either the AI evaluator or the legacy keyword matcher."""

    readiness_score: float = Field(ge=0, le=100)
    coverage_score: float = Field(ge=0, le=100)
    experience_level: str
    strong_matches: List[str] = Field(default_factory=list)
    needs_improvement: List[str] = Field(default_factory=list)
    critical_missing: List[str] = Field(default_factory=list)

    @field_validator("strong_matches", "needs_improvement", "critical_missing", mode="before")
    @classmethod
    def _coerce_items_to_str(cls, value):
        """Accept ["Python (Advanced)"] as well as legacy [("Python", 0.8)] tuples."""
        if value is None:
            return []
        coerced = []
        for item in value:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                name, weight = item
                coerced.append(f"{name} ({float(weight) * 100:.0f}%)")
            else:
                coerced.append(str(item))
        return coerced

    @field_validator("experience_level", mode="before")
    @classmethod
    def _stringify_experience_level(cls, value):
        return str(value) if value is not None else "Unknown"


# --------------------------------------------------------------------------
# Roadmap generation
# --------------------------------------------------------------------------

_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


class RoadmapTask(BaseModel):
    """A single actionable roadmap item, optionally carrying a resource link.

    RoadmapWeek stores tasks as plain markdown strings (so the UI can render
    the inline hyperlink as-is); this model exists for callers that want the
    task name and resource URL split apart, e.g. for analytics or export.
    """

    task_name: str
    resource_url: str = ""

    @classmethod
    def from_markdown(cls, raw_task: str) -> "RoadmapTask":
        match = _MARKDOWN_LINK_RE.search(raw_task or "")
        if match:
            url = match.group(2)
            name = _MARKDOWN_LINK_RE.sub(match.group(1), raw_task, count=1)
        else:
            url = ""
            name = raw_task or ""
        return cls(task_name=name.strip(), resource_url=url)


class RoadmapWeek(BaseModel):
    week_title: str
    tasks: List[str] = Field(default_factory=list)

    @field_validator("tasks", mode="before")
    @classmethod
    def _clean_tasks(cls, value):
        if not value:
            return []
        return [str(t).strip() for t in value if str(t).strip()]


class RoadmapResponse(BaseModel):
    weeks: List[RoadmapWeek] = Field(default_factory=list)

    @field_validator("weeks")
    @classmethod
    def _must_have_weeks(cls, value):
        if not value:
            raise ValueError("Roadmap must contain at least one week.")
        return value


# --------------------------------------------------------------------------
# External verification (LeetCode + GitHub)
# --------------------------------------------------------------------------

class LeetCodeStats(BaseModel):
    username: str
    easy: int = 0
    medium: int = 0
    hard: int = 0
    total: int = 0
    is_mock: bool = False


class GitHubStats(BaseModel):
    username: str
    public_repos: int = 0
    top_languages: List[str] = Field(default_factory=list)
    account_created: Optional[str] = None  # ISO date string, kept simple for prompt/report use

    @field_validator("account_created", mode="before")
    @classmethod
    def _normalize_date(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        return str(value)


class CandidateVerification(BaseModel):
    """Unified, LLM-prompt-ready bundle of every verified signal we have."""

    leetcode: Optional[LeetCodeStats] = None
    github: Optional[GitHubStats] = None

    def has_signal(self) -> bool:
        return self.leetcode is not None or self.github is not None

    def to_prompt_context(self) -> str:
        """Render a compact natural-language summary for the LLM prompt."""
        parts = []

        if self.leetcode:
            lc = self.leetcode
            mock_note = " (demo data — live API was unavailable)" if lc.is_mock else ""
            parts.append(
                f"The candidate's LeetCode profile ('{lc.username}') shows {lc.easy} Easy, "
                f"{lc.medium} Medium, and {lc.hard} Hard problems solved ({lc.total} total)"
                f"{mock_note}. Treat this as verified, ground-truth evidence of the candidate's "
                "real Data Structures & Algorithms / problem-solving ability. Where this signal "
                "disagrees with their self-reported proficiency for DSA-adjacent skills, trust the "
                "LeetCode evidence over the self-report."
            )

        if self.github:
            gh = self.github
            langs = ", ".join(gh.top_languages) if gh.top_languages else "no detectable primary language"
            created = f" GitHub account created {gh.account_created}." if gh.account_created else ""
            parts.append(
                f"The candidate's GitHub profile ('{gh.username}') has {gh.public_repos} public "
                f"repositories, with top languages: {langs}.{created} Treat consistent public "
                "activity in a language as light supporting evidence for that skill, but weight it "
                "less heavily than the LeetCode signal since repo activity doesn't verify depth."
            )

        if not parts:
            return "No verified coding-platform data was provided; rely on self-reported proficiency only."

        return " ".join(parts)
