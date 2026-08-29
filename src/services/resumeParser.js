/**
 * Resume text extraction and deterministic skill mapping.
 *
 * This module is intentionally free of any LLM calls -- extracting
 * *candidate* skill phrases from free-form resume text still goes through
 * analysisService.extractSkillsViaLLM, which calls LLMEngine. What lives
 * here is the deterministic part: getting raw text out of a .pdf/.txt
 * upload, and mapping a list of extracted tokens onto the curated
 * ALL_TECH_SKILLS catalog case-insensitively, with de-duplication.
 * Direct port of services/resume_parser.py.
 */
const pdfParse = require("pdf-parse");

async function extractTextFromUpload(filename, fileBuffer) {
  if (filename.toLowerCase().endsWith(".pdf")) {
    const parsed = await pdfParse(fileBuffer);
    return parsed.text || "";
  }
  return fileBuffer.toString("utf-8");
}

/** Trim, drop blanks, and de-duplicate while preserving first-seen order. */
function dedupeTokens(tokens) {
  const seen = new Set();
  const deduped = [];
  for (const raw of tokens) {
    const token = (raw || "").trim();
    if (!token) continue;
    const key = token.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(token);
  }
  return deduped;
}

/**
 * Map extracted tokens onto the curated skill catalog, case-insensitively.
 * Returns { known, custom }:
 *   - known: tokens that matched a catalog entry, normalized to the
 *     catalog's canonical casing/spelling, de-duplicated, order-preserved.
 *   - custom: de-duplicated tokens with no catalog match, so the UI can
 *     still offer them as free-text additions.
 */
function mapTokensToSkillCatalog(tokens, catalog) {
  const lookup = new Map(catalog.map((skill) => [skill.toLowerCase(), skill]));

  const known = [];
  const custom = [];

  for (const token of dedupeTokens(tokens)) {
    const canonical = lookup.get(token.toLowerCase());
    if (canonical) {
      if (!known.includes(canonical)) known.push(canonical);
    } else if (!custom.includes(token)) {
      custom.push(token);
    }
  }

  return { known, custom };
}

/**
 * Split a comma-separated string (e.g. LLM skill extraction output, or a
 * manual "Add custom skills" field) into clean tokens.
 */
function splitCommaList(rawText) {
  if (!rawText) return [];
  return dedupeTokens(rawText.split(","));
}

module.exports = {
  extractTextFromUpload,
  dedupeTokens,
  mapTokensToSkillCatalog,
  splitCommaList,
};
