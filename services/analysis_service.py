"""
Business logic layer: turns (role, skills, proficiencies, verification) into
a validated `AnalysisResult`, and (role, skills, gaps) into a validated
`RoadmapResponse`. Everything here is pure Python + LLMEngine -- no
Streamlit, no direct `requests` calls.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .llm_engine import LLMEngine, LLMEngineError
from .resume_parser import split_comma_list
from .schema import AnalysisResult, CandidateVerification, RoadmapResponse


# --------------------------------------------------------------------------
# Legacy deterministic analyzer (fallback when no LLM provider is configured
# or the AI call fails)
# --------------------------------------------------------------------------

def legacy_analyze_role(
    required_skills: List[str],
    skill_proficiency: Dict[str, float],
    experience_level: str,
) -> AnalysisResult:
    total_required = len(required_skills)

    strong_matches: List[str] = []
    needs_improvement: List[str] = []
    critical_missing: List[str] = []
    earned_weight_sum = 0.0
    covered_count = 0

    for requirement in required_skills:
        options = [opt.strip().lower() for opt in requirement.split("/")]
        matched_weights = [skill_proficiency[opt] for opt in options if opt in skill_proficiency]

        if matched_weights:
            best_weight = max(matched_weights)
            earned_weight_sum += best_weight
            covered_count += 1
            label = f"{requirement} ({best_weight * 100:.0f}%)"
            if best_weight >= 0.8:
                strong_matches.append(label)
            else:
                needs_improvement.append(label)
        else:
            critical_missing.append(requirement)

    coverage_score = (covered_count / total_required * 100) if total_required else 0.0
    readiness_score = (earned_weight_sum / total_required * 100) if total_required else 0.0

    return AnalysisResult(
        readiness_score=readiness_score,
        coverage_score=coverage_score,
        experience_level=experience_level,
        strong_matches=strong_matches,
        needs_improvement=needs_improvement,
        critical_missing=critical_missing,
    )


# --------------------------------------------------------------------------
# AI-driven analyzer
# --------------------------------------------------------------------------

def _build_analysis_prompt(
    target_role: str,
    required_skills: List[str],
    all_user_skills: List[str],
    skill_proficiencies: Dict[str, float],
    verification: Optional[CandidateVerification],
) -> str:
    proficiency_lines = ", ".join(
        f"{skill} ({weight * 100:.0f}% proficiency)" for skill, weight in skill_proficiencies.items()
    ) or "none provided"

    verification_context = (
        verification.to_prompt_context()
        if verification is not None
        else "No verified coding-platform data was provided; rely on self-reported proficiency only."
    )

    return (
        "Act as a Senior Technical Recruiter. Semantically evaluate a candidate's skills against "
        f"the required skills for the target role of {target_role}. "
        f"Required skills for this role: {required_skills}. "
        f"Candidate's stated skills: {all_user_skills}. "
        f"Candidate's proficiency levels: {proficiency_lines}. "
        f"{verification_context} "
        "Do not rely on exact string matching. If the candidate has an advanced or adjacent skill "
        "that demonstrates competence in a required skill (for example, knowing PyTorch implies "
        "competence in Feature Engineering or Machine Learning), credit them for it and note the "
        "inference in parentheses. "
        "Return ONLY a raw JSON object matching this exact schema, with no markdown formatting, "
        "no backticks, and no extra text before or after it: "
        '{"readiness_score": 85, "coverage_score": 90, "experience_level": '
        '"Mid to Senior", "strong_matches": ["Python (Advanced)", "Machine Learning (via PyTorch)"], '
        '"needs_improvement": ["Docker (Beginner)"], "critical_missing": ["Cloud Architecture"]}'
    )


def ai_analyze_role(
    engine: LLMEngine,
    target_role: str,
    required_skills: List[str],
    all_user_skills: List[str],
    skill_proficiencies: Dict[str, float],
    verification: Optional[CandidateVerification] = None,
) -> AnalysisResult:
    """Raises LLMEngineError if the provider chain fails or the response
    doesn't validate -- callers should catch this and fall back to
    `legacy_analyze_role`."""
    prompt = _build_analysis_prompt(
        target_role, required_skills, all_user_skills, skill_proficiencies, verification
    )
    return engine.generate_structured(prompt, AnalysisResult)


# --------------------------------------------------------------------------
# Resume skill extraction (LLM-assisted, deterministic mapping lives in
# resume_parser.py)
# --------------------------------------------------------------------------

def extract_skills_via_llm(engine: LLMEngine, resume_text: str) -> List[str]:
    """Ask the LLM to pull skill phrases out of raw resume text.

    Returns a plain list of candidate skill strings (not yet mapped against
    the curated catalog -- that's `resume_parser.map_tokens_to_skill_catalog`).
    Raises LLMEngineError on failure.
    """
    prompt = (
        "Extract all technical skills, programming languages, and frameworks from the "
        "following resume text. Return ONLY a comma-separated list of skills. Do not "
        f"include any other text, pleasantries, or markdown formatting. Text: {resume_text}"
    )
    raw_text = engine.generate_text(prompt)
    if not raw_text:
        raise LLMEngineError("AI resume extraction returned an empty response.")
    return split_comma_list(raw_text)


# --------------------------------------------------------------------------
# Roadmap generation
# --------------------------------------------------------------------------

def _build_roadmap_prompt(target_role: str, user_skills: List[str], missing_skills: List[str]) -> str:
    return (
        f"Act as a Senior Tech Recruiter and Mentor. The user wants to be a {target_role}. "
        f"They currently know {user_skills} with varying proficiencies. "
        f"They are completely missing these critical skills: {missing_skills}. "
        "Design a highly specific, no-nonsense 4-week learning roadmap to close this gap. "
        "Do not use generic filler like 'learn X' — every task should reference a concrete "
        "project, exercise, or resource type. "
        "Return ONLY a raw JSON object with no code fences and no extra text before or after it. "
        "It must match exactly this schema: "
        '{"weeks": [{"week_title": "Week 1: Fundamentals", "tasks": ["Task 1", "Task 2"]}]}. '
        "Include exactly 4 week objects, each with 3 to 5 concise, actionable tasks. "
        "CRITICAL: Every single task in the 'tasks' array MUST contain a clickable Markdown "
        "hyperlink pointing to a YouTube search query for that specific skill. Format the URL as "
        "[https://www.youtube.com/results?search_query=TOPIC+NAME+tutorial]"
        "(https://www.youtube.com/results?search_query=TOPIC+NAME+tutorial) "
        "(replace spaces with +). Example format for a task string inside the JSON: "
        "\"Build a basic CRUD app using [FastAPI]"
        "(https://www.youtube.com/results?search_query=FastAPI+tutorial) connected to a local "
        "SQLite database.\" "
        "CRITICAL: You must return valid, parseable JSON. Do NOT use double quotes inside "
        "your string values. Use single quotes for inner text (e.g., 'Learn Python' instead "
        'of "Learn Python"). Ensure all commas and brackets are perfectly formatted.'
    )


def generate_ai_roadmap(
    engine: LLMEngine,
    target_role: str,
    user_skills: List[str],
    missing_skills: List[str],
) -> RoadmapResponse:
    """Raises LLMEngineError if generation or schema validation fails."""
    prompt = _build_roadmap_prompt(target_role, user_skills, missing_skills)
    return engine.generate_structured(prompt, RoadmapResponse)
