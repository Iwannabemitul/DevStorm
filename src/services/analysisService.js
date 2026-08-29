/**
 * Business logic layer: turns (role, skills, proficiencies, verification)
 * into a validated analysis result, and (role, skills, gaps) into a
 * validated roadmap response. Direct port of services/analysis_service.py.
 */
const { LLMEngineError } = require("./llmEngine");
const { splitCommaList } = require("./resumeParser");
const { AnalysisResultSchema, RoadmapResponseSchema, verificationToPromptContext } = require("./schema");

// --------------------------------------------------------------------------
// Legacy deterministic analyzer (fallback when no LLM provider is configured
// or the AI call fails)
// --------------------------------------------------------------------------

function legacyAnalyzeRole(requiredSkills, skillProficiency, experienceLevel) {
  const totalRequired = requiredSkills.length;

  const strongMatches = [];
  const needsImprovement = [];
  const criticalMissing = [];
  let earnedWeightSum = 0.0;
  let coveredCount = 0;

  for (const requirement of requiredSkills) {
    const options = requirement.split("/").map((opt) => opt.trim().toLowerCase());
    const matchedWeights = options
      .filter((opt) => Object.prototype.hasOwnProperty.call(skillProficiency, opt))
      .map((opt) => skillProficiency[opt]);

    if (matchedWeights.length) {
      const bestWeight = Math.max(...matchedWeights);
      earnedWeightSum += bestWeight;
      coveredCount += 1;
      const label = `${requirement} (${(bestWeight * 100).toFixed(0)}%)`;
      if (bestWeight >= 0.8) {
        strongMatches.push(label);
      } else {
        needsImprovement.push(label);
      }
    } else {
      criticalMissing.push(requirement);
    }
  }

  const coverageScore = totalRequired ? (coveredCount / totalRequired) * 100 : 0.0;
  const readinessScore = totalRequired ? (earnedWeightSum / totalRequired) * 100 : 0.0;

  return AnalysisResultSchema.parse({
    readiness_score: readinessScore,
    coverage_score: coverageScore,
    experience_level: experienceLevel,
    strong_matches: strongMatches,
    needs_improvement: needsImprovement,
    critical_missing: criticalMissing,
  });
}

// --------------------------------------------------------------------------
// AI-driven analyzer
// --------------------------------------------------------------------------

function buildAnalysisPrompt(targetRole, requiredSkills, allUserSkills, skillProficiencies, verification) {
  const proficiencyEntries = Object.entries(skillProficiencies || {});
  const proficiencyLines = proficiencyEntries.length
    ? proficiencyEntries.map(([skill, weight]) => `${skill} (${(weight * 100).toFixed(0)}% proficiency)`).join(", ")
    : "none provided";

  const verificationContext = verificationToPromptContext(verification);

  return (
    "Act as a Senior Technical Recruiter. Semantically evaluate a candidate's skills against " +
    `the required skills for the target role of ${targetRole}. ` +
    `Required skills for this role: ${JSON.stringify(requiredSkills)}. ` +
    `Candidate's stated skills: ${JSON.stringify(allUserSkills)}. ` +
    `Candidate's proficiency levels: ${proficiencyLines}. ` +
    `${verificationContext} ` +
    "Do not rely on exact string matching. If the candidate has an advanced or adjacent skill " +
    "that demonstrates competence in a required skill (for example, knowing PyTorch implies " +
    "competence in Feature Engineering or Machine Learning), credit them for it and note the " +
    "inference in parentheses. " +
    "Return ONLY a raw JSON object matching this exact schema, with no markdown formatting, " +
    "no backticks, and no extra text before or after it: " +
    '{"readiness_score": 85, "coverage_score": 90, "experience_level": ' +
    '"Mid to Senior", "strong_matches": ["Python (Advanced)", "Machine Learning (via PyTorch)"], ' +
    '"needs_improvement": ["Docker (Beginner)"], "critical_missing": ["Cloud Architecture"]}'
  );
}

/**
 * Throws LLMEngineError if the provider chain fails or the response doesn't
 * validate -- callers should catch this and fall back to legacyAnalyzeRole.
 */
async function aiAnalyzeRole(engine, targetRole, requiredSkills, allUserSkills, skillProficiencies, verification = null) {
  const prompt = buildAnalysisPrompt(targetRole, requiredSkills, allUserSkills, skillProficiencies, verification);
  return engine.generateStructured(prompt, AnalysisResultSchema);
}

// --------------------------------------------------------------------------
// Resume skill extraction (LLM-assisted, deterministic mapping lives in
// resumeParser.js)
// --------------------------------------------------------------------------

/**
 * Ask the LLM to pull skill phrases out of raw resume text. Returns a plain
 * list of candidate skill strings (not yet mapped against the curated
 * catalog -- that's resumeParser.mapTokensToSkillCatalog). Throws
 * LLMEngineError on failure.
 */
async function extractSkillsViaLLM(engine, resumeText) {
  const prompt =
    "Extract all technical skills, programming languages, and frameworks from the " +
    "following resume text. Return ONLY a comma-separated list of skills. Do not " +
    `include any other text, pleasantries, or markdown formatting. Text: ${resumeText}`;
  const rawText = await engine.generateText(prompt);
  if (!rawText) {
    throw new LLMEngineError("AI resume extraction returned an empty response.");
  }
  return splitCommaList(rawText);
}

// --------------------------------------------------------------------------
// Roadmap generation
// --------------------------------------------------------------------------

function buildRoadmapPrompt(targetRole, userSkills, missingSkills) {
  return (
    `Act as a Senior Tech Recruiter and Mentor. The user wants to be a ${targetRole}. ` +
    `They currently know ${JSON.stringify(userSkills)} with varying proficiencies. ` +
    `They are completely missing these critical skills: ${JSON.stringify(missingSkills)}. ` +
    "Design a highly specific, no-nonsense 4-week learning roadmap to close this gap. " +
    "Do not use generic filler like 'learn X' — every task should reference a concrete " +
    "project, exercise, or resource type. " +
    "Return ONLY a raw JSON object with no code fences and no extra text before or after it. " +
    "It must match exactly this schema: " +
    '{"weeks": [{"week_title": "Week 1: Fundamentals", "tasks": ["Task 1", "Task 2"]}]}. ' +
    "Include exactly 4 week objects, each with 3 to 5 concise, actionable tasks. " +
    "CRITICAL: Every single task in the 'tasks' array MUST contain a clickable Markdown " +
    "hyperlink pointing to a YouTube search query for that specific skill. Format the URL as " +
    "[https://www.youtube.com/results?search_query=TOPIC+NAME+tutorial]" +
    "(https://www.youtube.com/results?search_query=TOPIC+NAME+tutorial) " +
    "(replace spaces with +). Example format for a task string inside the JSON: " +
    '"Build a basic CRUD app using [FastAPI]' +
    "(https://www.youtube.com/results?search_query=FastAPI+tutorial) connected to a local " +
    'SQLite database." ' +
    "CRITICAL: You must return valid, parseable JSON. Do NOT use double quotes inside " +
    "your string values. Use single quotes for inner text (e.g., 'Learn Python' instead " +
    'of "Learn Python"). Ensure all commas and brackets are perfectly formatted.'
  );
}

/** Throws LLMEngineError if generation or schema validation fails. */
async function generateAiRoadmap(engine, targetRole, userSkills, missingSkills) {
  const prompt = buildRoadmapPrompt(targetRole, userSkills, missingSkills);
  return engine.generateStructured(prompt, RoadmapResponseSchema);
}

module.exports = {
  legacyAnalyzeRole,
  aiAnalyzeRole,
  extractSkillsViaLLM,
  generateAiRoadmap,
};
