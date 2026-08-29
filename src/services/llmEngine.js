/**
 * LLMEngine: a singleton, provider-agnostic router.
 *
 * Direct port of services/llm_engine.py. Tries Gemini first, then falls
 * back to NVIDIA NIM models. Both providers are called over plain HTTPS via
 * axios instead of the Python SDKs.
 */
const axios = require("axios");

const GEMINI_MODEL_PRIORITY = [
  "models/gemini-2.0-flash",
  "models/gemini-1.5-flash",
  "models/gemini-1.5-pro",
  "models/gemini-pro",
];

const GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta";
const NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1";

// Ordered priority list for NVIDIA NIM models.
const NVIDIA_CANDIDATE_MODELS = [
  "google/diffusiongemma-26b-a4b-it",
  "moonshotai/kimi-k3",
  "meta/llama-3.3-70b-instruct",
  "mistralai/mistral-nemo-12b-instruct",
];

class LLMEngineError extends Error {}

class LLMEngine {
  constructor() {
    this._geminiApiKey = null;
    this._nvidiaApiKey = null;
  }

  static getInstance() {
    if (!LLMEngine._instance) {
      LLMEngine._instance = new LLMEngine();
    }
    return LLMEngine._instance;
  }

  configure({ geminiApiKey, nvidiaApiKey }) {
    this._geminiApiKey = geminiApiKey || null;
    this._nvidiaApiKey = nvidiaApiKey || null;
  }

  isConfigured() {
    return Boolean(this._geminiApiKey) || Boolean(this._nvidiaApiKey);
  }

  async _callGemini(prompt) {
    const listResp = await axios.get(`${GEMINI_API_BASE}/models`, {
      params: { key: this._geminiApiKey },
      timeout: 15000,
    });
    const availableModels = (listResp.data.models || [])
      .filter((m) => (m.supportedGenerationMethods || []).includes("generateContent"))
      .map((m) => m.name);

    let selectedModelName = GEMINI_MODEL_PRIORITY.find((candidate) => availableModels.includes(candidate));
    if (!selectedModelName && availableModels.length) {
      selectedModelName = availableModels[0];
    }
    if (!selectedModelName) {
      throw new Error("No Gemini models supporting generateContent are available.");
    }

    const genResp = await axios.post(
      `${GEMINI_API_BASE}/${selectedModelName}:generateContent`,
      { contents: [{ parts: [{ text: prompt }] }] },
      { params: { key: this._geminiApiKey }, timeout: 60000 }
    );

    const candidates = genResp.data.candidates || [];
    const text = (candidates[0]?.content?.parts || []).map((p) => p.text || "").join("").trim();
    if (!text) {
      throw new Error("Gemini returned an empty response.");
    }
    return text;
  }

  async _callNvidia(prompt) {
    const errors = [];

    for (const modelName of NVIDIA_CANDIDATE_MODELS) {
      try {
        const resp = await axios.post(
          `${NVIDIA_BASE_URL}/chat/completions`,
          {
            model: modelName,
            messages: [
              {
                role: "system",
                content:
                  "You are a senior technical evaluator. You must return only valid, " +
                  "well-formed JSON with no extra conversational text or markdown explanation.",
              },
              { role: "user", content: prompt },
            ],
            max_tokens: 4096,
            temperature: 0.2,
          },
          {
            headers: {
              Authorization: `Bearer ${this._nvidiaApiKey}`,
              "Content-Type": "application/json",
            },
            timeout: 60000,
          }
        );

        const choices = resp.data.choices || [];
        if (!choices.length) continue;

        const msg = choices[0].message || {};
        let text = (msg.content || "").trim();
        if (!text && msg.reasoning_content) {
          text = String(msg.reasoning_content).trim();
        }

        if (text) return text;
      } catch (exc) {
        const detail = exc.response ? JSON.stringify(exc.response.data) : exc.message;
        errors.push(`${modelName}: ${detail}`);
        continue;
      }
    }

    throw new Error(`NVIDIA candidates failed or returned empty: ${errors.join(" | ")}`);
  }

  /** Resilient router: try Gemini, then fall back to NVIDIA NIM models. */
  async generateText(prompt) {
    const errors = [];

    if (this._geminiApiKey) {
      try {
        return await this._callGemini(prompt);
      } catch (exc) {
        errors.push(`Gemini Error: ${exc.message}`);
      }
    }

    if (this._nvidiaApiKey) {
      try {
        return await this._callNvidia(prompt);
      } catch (exc) {
        errors.push(`NVIDIA Error: ${exc.message}`);
      }
    }

    if (errors.length) {
      throw new LLMEngineError(errors.join(" | "));
    }
    throw new LLMEngineError("No LLM provider is configured.");
  }

  static _stripCodeFences(text) {
    text = text.trim();
    if (text.startsWith("```")) {
      text = text.replace(/^`+|`+$/g, "").trim();
      if (text.toLowerCase().startsWith("json")) {
        text = text.slice(4);
      }
      text = text.trim();
    }
    return text;
  }

  static _isolateJsonObject(text) {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start === -1 || end === -1 || end < start) {
      throw new LLMEngineError(`No JSON object found in LLM response: ${text.slice(0, 150)}...`);
    }
    return text.slice(start, end + 1);
  }

  static _repairCommonJsonIssues(jsonStr) {
    jsonStr = jsonStr.replace(/\u201c|\u201d/g, '"');
    jsonStr = jsonStr.replace(/\u2018|\u2019/g, "'");
    jsonStr = jsonStr.replace(/,\s*([}\]])/g, "$1");
    jsonStr = jsonStr.replace(/\r/g, " ");
    return jsonStr;
  }

  static extractJson(rawText) {
    if (!rawText) {
      throw new LLMEngineError("Empty response from LLM provider.");
    }

    const text = LLMEngine._stripCodeFences(rawText);
    const jsonSlice = LLMEngine._isolateJsonObject(text);

    try {
      return JSON.parse(jsonSlice);
    } catch (exc) {
      const repaired = LLMEngine._repairCommonJsonIssues(jsonSlice);
      try {
        return JSON.parse(repaired);
      } catch (exc2) {
        throw new LLMEngineError(`Failed to parse JSON from LLM response: ${exc2.message}`);
      }
    }
  }

  /**
   * Runs the prompt, extracts JSON, and validates it against a zod schema.
   * @param {string} prompt
   * @param {import('zod').ZodSchema} schema
   */
  async generateStructured(prompt, schema) {
    const rawText = await this.generateText(prompt);
    const data = LLMEngine.extractJson(rawText);
    const result = schema.safeParse(data);
    if (!result.success) {
      throw new LLMEngineError(`LLM output failed schema validation: ${result.error.message}`);
    }
    return result.data;
  }
}

LLMEngine._instance = null;

module.exports = { LLMEngine, LLMEngineError };
