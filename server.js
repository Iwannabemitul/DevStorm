require("dotenv").config();

const path = require("path");
const express = require("express");
const cors = require("cors");

const apiRouter = require("./src/routes/api");

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json({ limit: "5mb" }));
app.use(express.urlencoded({ extended: true }));

app.use("/api", apiRouter);

app.use(express.static(path.join(__dirname, "public")));

app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, () => {
  console.log(`SkillGap Intelligence server running at http://localhost:${PORT}`);
  const engine = require("./src/services/llmEngine").LLMEngine.getInstance();
  engine.configure({
    geminiApiKey: process.env.GEMINI_API_KEY,
    nvidiaApiKey: process.env.NVIDIA_API_KEY,
  });
  if (!engine.isConfigured()) {
    console.warn(
      "No AI provider configured (GEMINI_API_KEY / NVIDIA_API_KEY). " +
        "AI features will be unavailable; gap analysis will fall back to the legacy keyword matcher."
    );
  }
});
