/**
 * Express API routes.
 *
 * This is the equivalent of the "cached wrappers around service calls"
 * section at the top of app.py: every intensive / network-bound / paid
 * service call is wrapped with an in-memory TTL cache (mirroring
 * @st.cache_data(ttl=3600, show_spinner=False)), and app.py's step machine
 * (render_step1..render_step4) becomes these HTTP endpoints, called by the
 * frontend's own step machine in public/js/app.js.
 */
const express = require("express");
const multer = require("multer");
const NodeCache = require("node-cache");

const { JOB_DATA, ALL_TECH_SKILLS, PROFICIENCY_OPTIONS, PROFICIENCY_WEIGHTS, FUN_FACTS } = require("../data/catalog");
const { LLMEngine, LLMEngineError } = require("../services/llmEngine");
const { extractTextFromUpload, mapTokensToSkillCatalog } = require("../services/resumeParser");
const { fetchLeetcodeStats, fetchGithubStats, buildCandidateVerification } = require("../services/externalApis");
const { legacyAnalyzeRole, aiAnalyzeRole, extractSkillsViaLLM, generateAiRoadmap } = require("../services/analysisService");
const { roadmapToMarkdown, buildMarkdownReport } = require("../services/report");

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } });

// TTL cache, mirrors @st.cache_data(ttl=3600) in the original app.
const cache = new NodeCache({ stdTTL: 3600, checkperiod: 120 });

async function cached(key, fn) {
  const hit = cache.get(key);
  if (hit !== undefined) return hit;
  const value = await fn();
  cache.set(key, value);
  return value;
}

function getEngine() {
  const engine = LLMEngine.getInstance();
  engine.configure({
    geminiApiKey: process.env.GEMINI_API_KEY,
    nvidiaApiKey: process.env.NVIDIA_API_KEY,
  });
  return engine;
}

// --------------------------------------------------------------------------
// Static reference data (catalog, proficiency options, fun facts)
// --------------------------------------------------------------------------

router.get("/catalog", (req, res) => {
  res.json({
    jobRoles: JOB_DATA.job_roles,
    allTechSkills: ALL_TECH_SKILLS,
    proficiencyOptions: PROFICIENCY_OPTIONS,
    proficiencyWeights: PROFICIENCY_WEIGHTS,
    funFacts: FUN_FACTS,
    aiConfigured: getEngine().isConfigured(),
  });
});

// --------------------------------------------------------------------------
// Step 1 -- resume upload + skill extraction
// --------------------------------------------------------------------------

router.post("/resume/extract", upload.single("resume"), async (req, res) => {
  const engine = getEngine();
  if (!req.file) {
    return res.status(400).json({ error: "Upload a PDF or TXT resume before extracting skills." });
  }
  if (!engine.isConfigured()) {
    return res.status(400).json({ error: "No AI provider is configured. Please contact the administrator." });
  }

  try {
    const resumeText = await cached(`text:${req.file.originalname}:${req.file.size}`, () =>
      extractTextFromUpload(req.file.originalname, req.file.buffer)
    );
    const rawTokens = await cached(`skills:${Buffer.from(resumeText).toString("base64").slice(0, 400)}`, () =>
      extractSkillsViaLLM(engine, resumeText)
    );
    const { known, custom } = mapTokensToSkillCatalog(rawTokens, ALL_TECH_SKILLS);
    res.json({ known, custom });
  } catch (exc) {
    const message = exc instanceof LLMEngineError ? exc.message : `Unexpected error: ${exc.message}`;
    res.status(502).json({ error: `Failed to extract skills: ${message}` });
  }
});

// --------------------------------------------------------------------------
// Step 1 -- LeetCode / GitHub verification
// --------------------------------------------------------------------------

router.post("/verify/leetcode", async (req, res) => {
  const username = (req.body.username || "").trim();
  const { data, note } = await cached(`leetcode:${username}`, () => fetchLeetcodeStats(username));
  res.json({ stats: data, note });
});

router.post("/verify/github", async (req, res) => {
  const username = (req.body.username || "").trim();
  const { data, note } = await cached(`github:${username}`, () => fetchGithubStats(username));
  res.json({ stats: data, note });
});

// --------------------------------------------------------------------------
// Step 3 -- analysis (AI evaluator with legacy keyword-match fallback)
// --------------------------------------------------------------------------

router.post("/analyze", async (req, res) => {
  const engine = getEngine();
  const { role, allUserSkills = [], skillProficiency = {}, leetcode = null, github = null } = req.body;

  const roleData = JOB_DATA.job_roles[role];
  if (!roleData) {
    return res.status(400).json({ error: `Unknown role: ${role}` });
  }
  const requiredSkills = roleData.required_skills;
  const experienceLevel = roleData.experience_level;

  const verification = buildCandidateVerification({ leetcode, github });

  let results;
  let aiError = null;
  try {
    if (!engine.isConfigured()) {
      throw new LLMEngineError("No AI provider configured.");
    }
    const cacheKey = `analyze:${role}:${JSON.stringify(allUserSkills)}:${JSON.stringify(
      Object.entries(skillProficiency).sort()
    )}:${JSON.stringify(verification)}`;
    results = await cached(cacheKey, () =>
      aiAnalyzeRole(engine, role, requiredSkills, allUserSkills, skillProficiency, verification)
    );
  } catch (exc) {
    console.error(`AI evaluation failed, falling back to legacy analyzer: ${exc.message}`);
    aiError = exc.message;
    results = legacyAnalyzeRole(requiredSkills, skillProficiency, experienceLevel);
  }

  let roadmapWeeks = null;
  let roadmapError = null;
  if (results.critical_missing.length && engine.isConfigured()) {
    try {
      const roadmapCacheKey = `roadmap:${role}:${JSON.stringify(allUserSkills)}:${JSON.stringify(results.critical_missing)}`;
      roadmapWeeks = await cached(roadmapCacheKey, () =>
        generateAiRoadmap(engine, role, allUserSkills, results.critical_missing)
      );
    } catch (exc) {
      console.error(`Roadmap generation/parsing failed: ${exc.message}`);
      roadmapError = exc.message;
    }
  }

  res.json({
    results,
    requiredSkills,
    aiError,
    roadmapWeeks,
    roadmapError,
  });
});

// --------------------------------------------------------------------------
// Report download (Markdown)
// --------------------------------------------------------------------------

router.post("/report", (req, res) => {
  const { role, results, roadmapWeeks } = req.body;
  if (!role || !results) {
    return res.status(400).json({ error: "role and results are required." });
  }
  const roadmapMarkdown = roadmapToMarkdown(roadmapWeeks);
  const markdown = buildMarkdownReport(role, results, roadmapMarkdown);
  res.setHeader("Content-Type", "text/markdown; charset=utf-8");
  res.setHeader("Content-Disposition", 'attachment; filename="SkillGap_Assessment_Report.md"');
  res.send(markdown);
});

module.exports = router;
