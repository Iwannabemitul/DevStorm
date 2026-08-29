"""
Multi-source candidate verification: LeetCode solve stats + GitHub public
activity, merged into a single `CandidateVerification` payload the prompt
layer can drop straight into an LLM call.

This module does no Streamlit I/O (no st.warning/st.toast) so it stays
unit-testable and cacheable with `st.cache_data` from app.py. Every
function returns `(data_or_none, note_or_none)` -- `note` is a short,
user-facing status string the UI layer can surface however it likes
(toast, warning, info), or `None` when nothing is worth mentioning.
"""
from __future__ import annotations

import collections
from typing import List, Optional, Tuple

import requests

from .schema import CandidateVerification, GitHubStats, LeetCodeStats

LEETCODE_SOLVED_URL = "https://alfa-leetcode-api.onrender.com/{username}/solved"
GITHUB_USER_URL = "https://api.github.com/users/{username}"
GITHUB_REPOS_URL = "https://api.github.com/users/{username}/repos"

_REQUEST_TIMEOUT_SECONDS = 8

# Shown when the LeetCode API is rate-limited or times out, so the demo/report
# flow can still proceed instead of dead-ending on a third-party outage.
_MOCK_LEETCODE_SOLVES = {"easy": 45, "medium": 120, "hard": 15, "total": 180}


# --------------------------------------------------------------------------
# LeetCode
# --------------------------------------------------------------------------

def fetch_leetcode_stats(username: str) -> Tuple[Optional[LeetCodeStats], Optional[str]]:
    """Fetch solved-problem counts for `username`.

    Falls back to mock demo data (flagged via `is_mock=True`) on a timeout or
    a 429, so a flaky/rate-limited third party never blocks the report.
    Returns (None, note) for a genuinely unknown username or any other
    unexpected failure.
    """
    username = (username or "").strip()
    if not username:
        return None, "Enter a LeetCode username first."

    url = LEETCODE_SOLVED_URL.format(username=username)
    try:
        response = requests.get(url, timeout=_REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        return (
            LeetCodeStats(username=username, is_mock=True, **_MOCK_LEETCODE_SOLVES),
            "LeetCode API timed out — showing demo profile data instead.",
        )
    except requests.exceptions.RequestException as exc:
        return None, f"Could not reach the LeetCode API: {exc}"

    if response.status_code == 404:
        return None, f"LeetCode username '{username}' was not found."

    if response.status_code == 429:
        return (
            LeetCodeStats(username=username, is_mock=True, **_MOCK_LEETCODE_SOLVES),
            "LeetCode API rate-limited — showing demo profile data instead.",
        )

    if response.status_code != 200:
        return None, f"LeetCode API returned an unexpected status ({response.status_code})."

    try:
        data = response.json()
    except ValueError:
        return None, "LeetCode API returned an unreadable response."

    stats = LeetCodeStats(
        username=username,
        easy=data.get("easySolved", 0),
        medium=data.get("mediumSolved", 0),
        hard=data.get("hardSolved", 0),
        total=data.get("solvedProblem", 0),
        is_mock=False,
    )
    return stats, f"Verified {stats.total} solved problems for '{username}'."


# --------------------------------------------------------------------------
# GitHub
# --------------------------------------------------------------------------

def _top_languages(repos: List[dict], limit: int = 3) -> List[str]:
    counts = collections.Counter(
        repo["language"] for repo in repos if repo.get("language")
    )
    return [language for language, _ in counts.most_common(limit)]


def fetch_github_stats(username: str) -> Tuple[Optional[GitHubStats], Optional[str]]:
    """Fetch public repo count, top languages, and account age for `username`.

    Falls back gracefully (returns None + a note) if the user doesn't exist
    or the API is rate-limited -- GitHub verification is a supporting
    signal, not a hard requirement, so failures here should never block the
    rest of the report.
    """
    username = (username or "").strip()
    if not username:
        return None, "Enter a GitHub username first."

    try:
        user_response = requests.get(
            GITHUB_USER_URL.format(username=username), timeout=_REQUEST_TIMEOUT_SECONDS
        )
    except requests.exceptions.RequestException as exc:
        return None, f"Could not reach the GitHub API: {exc}"

    if user_response.status_code == 404:
        return None, f"GitHub username '{username}' was not found."
    if user_response.status_code in (403, 429):
        return None, "GitHub API rate limit reached — continuing without GitHub data."
    if user_response.status_code != 200:
        return None, f"GitHub API returned an unexpected status ({user_response.status_code})."

    try:
        user_data = user_response.json()
    except ValueError:
        return None, "GitHub API returned an unreadable user response."

    try:
        repos_response = requests.get(
            GITHUB_REPOS_URL.format(username=username),
            params={"per_page": 100, "type": "owner"},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        repos = repos_response.json() if repos_response.status_code == 200 else []
        if not isinstance(repos, list):
            repos = []
    except (requests.exceptions.RequestException, ValueError):
        repos = []

    stats = GitHubStats(
        username=username,
        public_repos=user_data.get("public_repos", len(repos)),
        top_languages=_top_languages(repos),
        account_created=user_data.get("created_at"),
    )
    return stats, f"Verified GitHub profile for '{username}' ({stats.public_repos} public repos)."


# --------------------------------------------------------------------------
# Unified payload
# --------------------------------------------------------------------------

def build_candidate_verification(
    leetcode_stats: Optional[LeetCodeStats],
    github_stats: Optional[GitHubStats],
) -> CandidateVerification:
    """Combine already-fetched stats into the single payload the prompt layer uses.

    Fetching stays the caller's job (usually behind `st.cache_data`) so this
    function is a pure, trivially-testable assembly step.
    """
    return CandidateVerification(leetcode=leetcode_stats, github=github_stats)
