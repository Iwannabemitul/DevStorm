/**
 * Multi-source candidate verification: LeetCode solve stats + GitHub public
 * activity, merged into a single verification payload the prompt layer can
 * drop straight into an LLM call.
 *
 * Every function returns { data: dataOrNull, note: noteOrNull } -- `note` is
 * a short, user-facing status string the UI layer can surface however it
 * likes (toast, warning, info), or null when nothing is worth mentioning.
 * Direct port of services/external_apis.py.
 */
const axios = require("axios");

const LEETCODE_SOLVED_URL = (username) => `https://alfa-leetcode-api.onrender.com/${encodeURIComponent(username)}/solved`;
const GITHUB_USER_URL = (username) => `https://api.github.com/users/${encodeURIComponent(username)}`;
const GITHUB_REPOS_URL = (username) => `https://api.github.com/users/${encodeURIComponent(username)}/repos`;

const REQUEST_TIMEOUT_MS = 8000;

// Shown when the LeetCode API is rate-limited or times out, so the demo/report
// flow can still proceed instead of dead-ending on a third-party outage.
const MOCK_LEETCODE_SOLVES = { easy: 45, medium: 120, hard: 15, total: 180 };

// --------------------------------------------------------------------------
// LeetCode
// --------------------------------------------------------------------------

async function fetchLeetcodeStats(usernameRaw) {
  const username = (usernameRaw || "").trim();
  if (!username) {
    return { data: null, note: "Enter a LeetCode username first." };
  }

  let response;
  try {
    response = await axios.get(LEETCODE_SOLVED_URL(username), {
      timeout: REQUEST_TIMEOUT_MS,
      validateStatus: () => true,
    });
  } catch (exc) {
    if (exc.code === "ECONNABORTED") {
      return {
        data: { username, is_mock: true, ...MOCK_LEETCODE_SOLVES },
        note: "LeetCode API timed out — showing demo profile data instead.",
      };
    }
    return { data: null, note: `Could not reach the LeetCode API: ${exc.message}` };
  }

  if (response.status === 404) {
    return { data: null, note: `LeetCode username '${username}' was not found.` };
  }

  if (response.status === 429) {
    return {
      data: { username, is_mock: true, ...MOCK_LEETCODE_SOLVES },
      note: "LeetCode API rate-limited — showing demo profile data instead.",
    };
  }

  if (response.status !== 200) {
    return { data: null, note: `LeetCode API returned an unexpected status (${response.status}).` };
  }

  const data = response.data;
  if (!data || typeof data !== "object") {
    return { data: null, note: "LeetCode API returned an unreadable response." };
  }

  const stats = {
    username,
    easy: data.easySolved || 0,
    medium: data.mediumSolved || 0,
    hard: data.hardSolved || 0,
    total: data.solvedProblem || 0,
    is_mock: false,
  };
  return { data: stats, note: `Verified ${stats.total} solved problems for '${username}'.` };
}

// --------------------------------------------------------------------------
// GitHub
// --------------------------------------------------------------------------

function topLanguages(repos, limit = 3) {
  const counts = new Map();
  for (const repo of repos) {
    if (repo && repo.language) {
      counts.set(repo.language, (counts.get(repo.language) || 0) + 1);
    }
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([language]) => language);
}

async function fetchGithubStats(usernameRaw) {
  const username = (usernameRaw || "").trim();
  if (!username) {
    return { data: null, note: "Enter a GitHub username first." };
  }

  let userResponse;
  try {
    userResponse = await axios.get(GITHUB_USER_URL(username), {
      timeout: REQUEST_TIMEOUT_MS,
      validateStatus: () => true,
    });
  } catch (exc) {
    return { data: null, note: `Could not reach the GitHub API: ${exc.message}` };
  }

  if (userResponse.status === 404) {
    return { data: null, note: `GitHub username '${username}' was not found.` };
  }
  if (userResponse.status === 403 || userResponse.status === 429) {
    return { data: null, note: "GitHub API rate limit reached — continuing without GitHub data." };
  }
  if (userResponse.status !== 200) {
    return { data: null, note: `GitHub API returned an unexpected status (${userResponse.status}).` };
  }

  const userData = userResponse.data;
  if (!userData || typeof userData !== "object") {
    return { data: null, note: "GitHub API returned an unreadable user response." };
  }

  let repos = [];
  try {
    const reposResponse = await axios.get(GITHUB_REPOS_URL(username), {
      params: { per_page: 100, type: "owner" },
      timeout: REQUEST_TIMEOUT_MS,
      validateStatus: () => true,
    });
    repos = reposResponse.status === 200 && Array.isArray(reposResponse.data) ? reposResponse.data : [];
  } catch {
    repos = [];
  }

  const stats = {
    username,
    public_repos: userData.public_repos ?? repos.length,
    top_languages: topLanguages(repos),
    account_created: userData.created_at || null,
  };
  return { data: stats, note: `Verified GitHub profile for '${username}' (${stats.public_repos} public repos).` };
}

// --------------------------------------------------------------------------
// Unified payload
// --------------------------------------------------------------------------

/**
 * Combine already-fetched stats into the single payload the prompt layer
 * uses. Fetching stays the caller's job so this stays a pure assembly step.
 */
function buildCandidateVerification({ leetcode, github }) {
  return { leetcode: leetcode || null, github: github || null };
}

module.exports = {
  fetchLeetcodeStats,
  fetchGithubStats,
  buildCandidateVerification,
};
