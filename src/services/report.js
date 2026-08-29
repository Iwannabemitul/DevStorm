/**
 * Formatting helpers that turn validated result objects into the strings
 * offered for download. Pure functions. Direct port of ui/report.py.
 */

/** Build export Markdown without escaping task text, preserving inline links. */
function roadmapToMarkdown(roadmap) {
  if (!roadmap || !roadmap.weeks || !roadmap.weeks.length) {
    return "_No AI roadmap was generated for this assessment._";
  }

  const lines = [];
  for (const week of roadmap.weeks) {
    lines.push(`### ${week.week_title}`);
    for (const task of week.tasks) {
      lines.push(`- [ ] ${task}`);
    }
    lines.push("");
  }

  return lines.join("\n").trim();
}

function buildMarkdownReport(role, results, roadmapText) {
  const lines = [
    `# SkillGap Assessment Report: ${role}`,
    "",
    `**Experience Level:** ${results.experience_level}`,
    "",
    `**Role Readiness:** ${results.readiness_score.toFixed(0)}%`,
    `**Skill Coverage:** ${results.coverage_score.toFixed(0)}%`,
    "",
    "## Strong Matches",
  ];
  if (results.strong_matches && results.strong_matches.length) {
    lines.push(...results.strong_matches.map((item) => `- ${item}`));
  } else {
    lines.push("- None yet.");
  }

  lines.push("");
  lines.push("## Needs Improvement");
  if (results.needs_improvement && results.needs_improvement.length) {
    lines.push(...results.needs_improvement.map((item) => `- ${item}`));
  } else {
    lines.push("- Nothing stuck at Beginner level.");
  }

  lines.push("");
  lines.push("## Critical Gaps");
  if (results.critical_missing && results.critical_missing.length) {
    lines.push(...results.critical_missing.map((req) => `- ${req}`));
  } else {
    lines.push("- None. Full coverage.");
  }

  lines.push("");
  lines.push("## 4-Week AI Roadmap");
  lines.push("");
  lines.push(roadmapText || "_No AI roadmap was generated for this assessment._");

  return lines.join("\n");
}

module.exports = { roadmapToMarkdown, buildMarkdownReport };
