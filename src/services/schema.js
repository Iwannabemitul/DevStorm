/**
 * Zod schemas shared across the service layer.
 *
 * Every value that comes back from an LLM call or a third-party API gets
 * validated against one of these schemas before it is trusted by the rest
 * of the app. Direct port of the original services/schema.py -- no raw
 * parsed JSON crosses a service boundary unvalidated.
 */
const { z } = require("zod");

// --------------------------------------------------------------------------
// Skill-gap analysis
// --------------------------------------------------------------------------

/** Accept ["Python (Advanced)"] as well as legacy [["Python", 0.8]] pairs. */
function coerceItemsToStr(value) {
  if (value == null) return [];
  return value.map((item) => {
    if (Array.isArray(item) && item.length === 2) {
      const [name, weight] = item;
      return `${name} (${(Number(weight) * 100).toFixed(0)}%)`;
    }
    return String(item);
  });
}

const AnalysisResultSchema = z
  .object({
    readiness_score: z.number().min(0).max(100),
    coverage_score: z.number().min(0).max(100),
    experience_level: z.preprocess((v) => (v == null ? "Unknown" : String(v)), z.string()),
    strong_matches: z.preprocess(coerceItemsToStr, z.array(z.string())).default([]),
    needs_improvement: z.preprocess(coerceItemsToStr, z.array(z.string())).default([]),
    critical_missing: z.preprocess(coerceItemsToStr, z.array(z.string())).default([]),
  })
  .passthrough();

// --------------------------------------------------------------------------
// Roadmap generation
// --------------------------------------------------------------------------

const RoadmapWeekSchema = z.object({
  week_title: z.string(),
  tasks: z.preprocess(
    (value) => (!value ? [] : value.map((t) => String(t).trim()).filter(Boolean)),
    z.array(z.string())
  ).default([]),
});

const RoadmapResponseSchema = z.object({
  weeks: z.array(RoadmapWeekSchema).min(1, "Roadmap must contain at least one week."),
});

// --------------------------------------------------------------------------
// External verification (LeetCode + GitHub)
// --------------------------------------------------------------------------

const LeetCodeStatsSchema = z.object({
  username: z.string(),
  easy: z.number().default(0),
  medium: z.number().default(0),
  hard: z.number().default(0),
  total: z.number().default(0),
  is_mock: z.boolean().default(false),
});

const GitHubStatsSchema = z.object({
  username: z.string(),
  public_repos: z.number().default(0),
  top_languages: z.array(z.string()).default([]),
  account_created: z.preprocess((v) => {
    if (v == null) return null;
    if (v instanceof Date) return v.toISOString().slice(0, 10);
    return String(v);
  }, z.string().nullable()).default(null),
});

/** Render a compact natural-language summary for the LLM prompt. */
function verificationToPromptContext(verification) {
  const parts = [];

  if (verification && verification.leetcode) {
    const lc = verification.leetcode;
    const mockNote = lc.is_mock ? " (demo data — live API was unavailable)" : "";
    parts.push(
      `The candidate's LeetCode profile ('${lc.username}') shows ${lc.easy} Easy, ` +
        `${lc.medium} Medium, and ${lc.hard} Hard problems solved (${lc.total} total)` +
        `${mockNote}. Treat this as verified, ground-truth evidence of the candidate's ` +
        "real Data Structures & Algorithms / problem-solving ability. Where this signal " +
        "disagrees with their self-reported proficiency for DSA-adjacent skills, trust the " +
        "LeetCode evidence over the self-report."
    );
  }

  if (verification && verification.github) {
    const gh = verification.github;
    const langs = gh.top_languages && gh.top_languages.length ? gh.top_languages.join(", ") : "no detectable primary language";
    const created = gh.account_created ? ` GitHub account created ${gh.account_created}.` : "";
    parts.push(
      `The candidate's GitHub profile ('${gh.username}') has ${gh.public_repos} public ` +
        `repositories, with top languages: ${langs}.${created} Treat consistent public ` +
        "activity in a language as light supporting evidence for that skill, but weight it " +
        "less heavily than the LeetCode signal since repo activity doesn't verify depth."
    );
  }

  if (!parts.length) {
    return "No verified coding-platform data was provided; rely on self-reported proficiency only.";
  }

  return parts.join(" ");
}

module.exports = {
  AnalysisResultSchema,
  RoadmapWeekSchema,
  RoadmapResponseSchema,
  LeetCodeStatsSchema,
  GitHubStatsSchema,
  verificationToPromptContext,
};
