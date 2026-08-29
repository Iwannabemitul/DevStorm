"""Formatting helpers that turn validated schema objects into the strings the
UI displays or offers for download. Pure functions, no Streamlit calls."""
from __future__ import annotations

from typing import Optional

from services.schema import AnalysisResult, RoadmapResponse


def roadmap_to_markdown(roadmap: Optional[RoadmapResponse]) -> str:
    """Build export Markdown without escaping task text, preserving inline links."""
    if not roadmap or not roadmap.weeks:
        return "_No AI roadmap was generated for this assessment._"

    lines = []
    for week in roadmap.weeks:
        lines.append(f"### {week.week_title}")
        for task in week.tasks:
            lines.append(f"- [ ] {task}")
        lines.append("")

    return "\n".join(lines).strip()


def build_markdown_report(role: str, results: AnalysisResult, roadmap_text: str) -> str:
    lines = [
        f"# SkillGap Assessment Report: {role}",
        "",
        f"**Experience Level:** {results.experience_level}",
        "",
        f"**Role Readiness:** {results.readiness_score:.0f}%",
        f"**Skill Coverage:** {results.coverage_score:.0f}%",
        "",
        "## Strong Matches",
    ]
    if results.strong_matches:
        lines.extend(f"- {item}" for item in results.strong_matches)
    else:
        lines.append("- None yet.")

    lines.append("")
    lines.append("## Needs Improvement")
    if results.needs_improvement:
        lines.extend(f"- {item}" for item in results.needs_improvement)
    else:
        lines.append("- Nothing stuck at Beginner level.")

    lines.append("")
    lines.append("## Critical Gaps")
    if results.critical_missing:
        lines.extend(f"- {req}" for req in results.critical_missing)
    else:
        lines.append("- None. Full coverage.")

    lines.append("")
    lines.append("## 4-Week AI Roadmap")
    lines.append("")
    lines.append(roadmap_text if roadmap_text else "_No AI roadmap was generated for this assessment._")

    return "\n".join(lines)
