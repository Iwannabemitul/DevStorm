/**
 * SkillGap Intelligence -- frontend step machine.
 *
 * This is the browser-side equivalent of app.py's session-state step
 * machine (render_step0 .. render_step4). All heavy lifting (LLM calls,
 * third-party verification, JSON schema validation) stays server-side in
 * /api/*; this file only owns UI state and wiring.
 */
(() => {
  "use strict";

  // ------------------------------------------------------------------
  // State (mirrors app.py's st.session_state defaults)
  // ------------------------------------------------------------------
  const state = {
    step: 0,
    inputMode: null,
    parsedKnownSkills: [],
    parsedCustomSkills: "",
    allUserSkills: [],
    skillProficiency: {}, // lowercased skill name -> weight
    leetcodeStats: null,
    githubStats: null,
    selectedRole: null,
    lastResults: null,
    lastRole: null,
    lastRequiredSkills: [],
    lastSkillProficiency: {},
    lastRoadmapWeeks: null,
    lastRoadmapError: null,
    lastAiError: null,
    manualSelected: [],
  };

  let catalog = null; // { jobRoles, allTechSkills, proficiencyOptions, proficiencyWeights, funFacts, aiConfigured }
  let radarChart = null;
  let barChart = null;
  let funFactTimer = null;

  const $ = (sel) => document.querySelector(sel);
  const $all = (sel) => Array.from(document.querySelectorAll(sel));

  function showToast(message) {
    const toast = $("#toast");
    toast.textContent = message;
    toast.classList.remove("hidden");
    toast.style.opacity = "1";
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.classList.add("hidden"), 300);
    }, 3200);
  }

  // ------------------------------------------------------------------
  // Step navigation
  // ------------------------------------------------------------------
  function goToStep(n) {
    state.step = n;
    $all(".step").forEach((el) => el.classList.add("hidden"));
    $(`#step-${n}`).classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function resetApp() {
    state.step = 0;
    state.inputMode = null;
    state.parsedKnownSkills = [];
    state.parsedCustomSkills = "";
    state.allUserSkills = [];
    state.skillProficiency = {};
    state.leetcodeStats = null;
    state.githubStats = null;
    state.selectedRole = null;
    state.lastResults = null;
    state.lastRole = null;
    state.lastRequiredSkills = [];
    state.lastSkillProficiency = {};
    state.lastRoadmapWeeks = null;
    state.lastRoadmapError = null;
    state.lastAiError = null;
    state.manualSelected = [];

    $("#resume-file").value = "";
    $("#resume-extra-skills").value = "";
    $("#manual-custom-skills").value = "";
    $("#manual-search").value = "";
    $("#leetcode-username").value = "";
    $("#github-username").value = "";
    $("#leetcode-result").textContent = "";
    $("#github-result").textContent = "";
    $("#extract-status").textContent = "";
    $("#detected-skills-wrap").classList.add("hidden");

    renderManualChips();
    renderProficiencyList();
    goToStep(0);
  }

  // ------------------------------------------------------------------
  // Catalog bootstrap
  // ------------------------------------------------------------------
  async function loadCatalog() {
    const resp = await fetch("/api/catalog");
    catalog = await resp.json();

    const roleSelect = $("#role-select");
    roleSelect.innerHTML = "";
    Object.keys(catalog.jobRoles).forEach((role) => {
      const opt = document.createElement("option");
      opt.value = role;
      opt.textContent = role;
      roleSelect.appendChild(opt);
    });

    renderManualOptions("");
  }

  // ------------------------------------------------------------------
  // Step 0 -- entry mode
  // ------------------------------------------------------------------
  $("#btn-mode-resume").addEventListener("click", () => {
    state.inputMode = "resume";
    $("#resume-panel").classList.remove("hidden");
    $("#manual-panel").classList.add("hidden");
    goToStep(1);
    recomputeAllUserSkills();
  });

  $("#btn-mode-manual").addEventListener("click", () => {
    state.inputMode = "manual";
    $("#manual-panel").classList.remove("hidden");
    $("#resume-panel").classList.add("hidden");
    goToStep(1);
    recomputeAllUserSkills();
  });

  // ------------------------------------------------------------------
  // Step 1 -- resume mode
  // ------------------------------------------------------------------
  $("#btn-extract").addEventListener("click", async () => {
    const fileInput = $("#resume-file");
    const statusEl = $("#extract-status");
    if (!fileInput.files.length) {
      statusEl.textContent = "Upload a PDF or TXT resume before extracting skills.";
      return;
    }
    if (!catalog.aiConfigured) {
      statusEl.textContent = "No AI provider is configured. Please contact the administrator.";
      return;
    }

    statusEl.textContent = "Extracting skills from resume...";
    const formData = new FormData();
    formData.append("resume", fileInput.files[0]);

    try {
      const resp = await fetch("/api/resume/extract", { method: "POST", body: formData });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Extraction failed.");

      state.parsedKnownSkills = data.known;
      state.parsedCustomSkills = data.custom.join(", ");
      $("#resume-extra-skills").value = state.parsedCustomSkills;
      statusEl.textContent = "Skills extracted and applied below.";
      renderDetectedSkills();
      recomputeAllUserSkills();
    } catch (exc) {
      statusEl.textContent = `Failed to extract skills: ${exc.message}`;
    }
  });

  function renderDetectedSkills() {
    const detected = dedupe([...state.parsedKnownSkills, ...splitCommaList(state.parsedCustomSkills)]);
    const wrap = $("#detected-skills-wrap");
    if (!detected.length) {
      wrap.classList.add("hidden");
      return;
    }
    wrap.classList.remove("hidden");
    $("#detected-skills").textContent = detected.join(", ");
  }

  $("#resume-extra-skills").addEventListener("input", () => {
    state.parsedCustomSkills = $("#resume-extra-skills").value;
    renderDetectedSkills();
    recomputeAllUserSkills();
  });

  // ------------------------------------------------------------------
  // Step 1 -- manual mode multiselect
  // ------------------------------------------------------------------
  function renderManualOptions(query) {
    const box = $("#manual-options");
    if (!catalog) return;
    const q = query.trim().toLowerCase();
    const matches = catalog.allTechSkills
      .filter((s) => !state.manualSelected.includes(s))
      .filter((s) => !q || s.toLowerCase().includes(q))
      .slice(0, 40);

    if (!matches.length || document.activeElement !== $("#manual-search")) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }
    box.classList.remove("hidden");
    box.innerHTML = "";
    matches.forEach((skill) => {
      const div = document.createElement("div");
      div.className = "multiselect-option";
      div.textContent = skill;
      div.addEventListener("mousedown", (e) => {
        e.preventDefault();
        addManualSkill(skill);
      });
      box.appendChild(div);
    });
  }

  function addManualSkill(skill) {
    if (!state.manualSelected.includes(skill)) {
      state.manualSelected.push(skill);
    }
    $("#manual-search").value = "";
    renderManualOptions("");
    renderManualChips();
    recomputeAllUserSkills();
  }

  function removeManualSkill(skill) {
    state.manualSelected = state.manualSelected.filter((s) => s !== skill);
    renderManualChips();
    recomputeAllUserSkills();
  }

  function renderManualChips() {
    const row = $("#manual-chips");
    row.innerHTML = "";
    state.manualSelected.forEach((skill) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.innerHTML = `${escapeHtml(skill)} <button type="button" aria-label="Remove ${escapeHtml(skill)}">×</button>`;
      chip.querySelector("button").addEventListener("click", () => removeManualSkill(skill));
      row.appendChild(chip);
    });
  }

  $("#manual-search").addEventListener("input", (e) => renderManualOptions(e.target.value));
  $("#manual-search").addEventListener("focus", (e) => renderManualOptions(e.target.value));
  document.addEventListener("click", (e) => {
    if (!$("#manual-multiselect").contains(e.target)) {
      $("#manual-options").classList.add("hidden");
    }
  });

  $("#manual-custom-skills").addEventListener("input", recomputeAllUserSkills);

  // ------------------------------------------------------------------
  // Step 1 -- combined skill list + proficiency
  // ------------------------------------------------------------------
  function recomputeAllUserSkills() {
    let combined;
    if (state.inputMode === "resume") {
      combined = dedupe([...state.parsedKnownSkills, ...splitCommaList($("#resume-extra-skills").value)]);
    } else {
      combined = dedupe([...state.manualSelected, ...splitCommaList($("#manual-custom-skills").value)]);
    }
    state.allUserSkills = combined;
    renderProficiencyList();
  }

  function renderProficiencyList() {
    const list = $("#proficiency-list");
    const section = $("#proficiency-section");
    const empty = $("#proficiency-empty");

    if (!state.allUserSkills.length) {
      section.classList.add("hidden");
      empty.classList.remove("hidden");
      state.skillProficiency = {};
      return;
    }
    section.classList.remove("hidden");
    empty.classList.add("hidden");

    const options = (catalog && catalog.proficiencyOptions) || ["Beginner (0.4)", "Intermediate (0.8)", "Advanced (1.0)"];
    const weights = (catalog && catalog.proficiencyWeights) || {
      "Beginner (0.4)": 0.4,
      "Intermediate (0.8)": 0.8,
      "Advanced (1.0)": 1.0,
    };

    // Preserve already-chosen proficiency selections where possible.
    const prevSelections = {};
    $all(".prof-row select").forEach((sel) => {
      prevSelections[sel.dataset.skill] = sel.value;
    });

    list.innerHTML = "";
    state.allUserSkills.forEach((skill) => {
      const row = document.createElement("div");
      row.className = "prof-row";

      const name = document.createElement("span");
      name.className = "prof-name";
      name.textContent = skill;

      const select = document.createElement("select");
      select.dataset.skill = skill;
      options.forEach((opt) => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt;
        select.appendChild(o);
      });
      select.value = prevSelections[skill] || "Intermediate (0.8)";

      select.addEventListener("change", () => {
        state.skillProficiency[skill.trim().toLowerCase()] = weights[select.value];
      });

      row.appendChild(name);
      row.appendChild(select);
      list.appendChild(row);

      state.skillProficiency[skill.trim().toLowerCase()] = weights[select.value];
    });
  }

  // ------------------------------------------------------------------
  // Step 1 -- verification
  // ------------------------------------------------------------------
  $("#btn-verify-leetcode").addEventListener("click", async () => {
    const username = $("#leetcode-username").value.trim();
    const resultEl = $("#leetcode-result");
    resultEl.textContent = "Checking LeetCode profile...";
    try {
      const resp = await fetch("/api/verify/leetcode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      });
      const data = await resp.json();
      if (data.stats) {
        state.leetcodeStats = data.stats;
        showToast(data.note || "LeetCode verified.");
        const s = data.stats;
        const mockTag = s.is_mock ? " (demo data)" : "";
        resultEl.innerHTML = `✅ ${escapeHtml(s.username)}${mockTag}: ${s.easy} Easy · ${s.medium} Medium · ${s.hard} Hard (${s.total} total solved)`;
      } else {
        resultEl.textContent = data.note || "Could not verify LeetCode profile.";
      }
    } catch (exc) {
      resultEl.textContent = `Error: ${exc.message}`;
    }
  });

  $("#btn-verify-github").addEventListener("click", async () => {
    const username = $("#github-username").value.trim();
    const resultEl = $("#github-result");
    resultEl.textContent = "Checking GitHub profile...";
    try {
      const resp = await fetch("/api/verify/github", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      });
      const data = await resp.json();
      if (data.stats) {
        state.githubStats = data.stats;
        showToast(data.note || "GitHub verified.");
        const g = data.stats;
        const langs = g.top_languages.length ? g.top_languages.join(", ") : "no detectable language";
        const created = g.account_created ? ` · since ${g.account_created.slice(0, 10)}` : "";
        resultEl.innerHTML = `✅ ${escapeHtml(g.username)}: ${g.public_repos} public repos · top languages: ${escapeHtml(langs)}${created}`;
      } else {
        resultEl.textContent = data.note || "Could not verify GitHub profile.";
      }
    } catch (exc) {
      resultEl.textContent = `Error: ${exc.message}`;
    }
  });

  // ------------------------------------------------------------------
  // Step 1 -- nav
  // ------------------------------------------------------------------
  $("#btn-back-to-0").addEventListener("click", () => goToStep(0));

  $("#btn-continue-to-2").addEventListener("click", () => {
    recomputeAllUserSkills();
    if (!state.allUserSkills.length) {
      showToast("Select or enter at least one skill before continuing.");
      return;
    }
    goToStep(2);
  });

  // ------------------------------------------------------------------
  // Step 2 -- target role
  // ------------------------------------------------------------------
  $("#btn-back-to-1").addEventListener("click", () => goToStep(1));

  $("#btn-generate").addEventListener("click", async () => {
    state.selectedRole = $("#role-select").value;
    goToStep(3);
    await runAnalysis();
  });

  // ------------------------------------------------------------------
  // Step 3 -- analysis (processing)
  // ------------------------------------------------------------------
  function startFunFacts() {
    const facts = [...(catalog.funFacts || [])];
    for (let i = facts.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [facts[i], facts[j]] = [facts[j], facts[i]];
    }
    const el = $("#fun-fact-text");
    clearInterval(funFactTimer);
    funFactTimer = setInterval(() => {
      if (!el) return;
      el.style.opacity = 0;
      setTimeout(() => {
        el.textContent = facts[Math.floor(Math.random() * facts.length)];
        el.style.opacity = 1;
      }, 400);
    }, 2500);
  }

  async function runAnalysis() {
    $("#building-for-role").textContent = `Building your report for ${state.selectedRole}`;
    startFunFacts();

    try {
      const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: state.selectedRole,
          allUserSkills: state.allUserSkills,
          skillProficiency: state.skillProficiency,
          leetcode: state.leetcodeStats,
          github: state.githubStats,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Analysis failed.");

      state.lastResults = data.results;
      state.lastRole = state.selectedRole;
      state.lastRequiredSkills = data.requiredSkills;
      state.lastSkillProficiency = { ...state.skillProficiency };
      state.lastRoadmapWeeks = data.roadmapWeeks;
      state.lastRoadmapError = data.roadmapError;
      state.lastAiError = data.aiError;
    } catch (exc) {
      state.lastResults = null;
      state.lastAiError = exc.message;
    } finally {
      clearInterval(funFactTimer);
      renderResults();
      goToStep(4);
      if (state.lastResults) {
        showToast("🎉 Your report is ready!");
        playCompletionChime();
      }
    }
  }

  function playCompletionChime() {
    try {
      const audio = new Audio("https://assets.mixkit.co/active_storage/sfx/212/212-preview.mp3");
      audio.volume = 0.4;
      audio.play().catch(() => {
        /* Autoplay can be blocked by the browser; that's fine, it's a non-essential cue. */
      });
    } catch {
      /* Ignore -- purely decorative. */
    }
  }

  // ------------------------------------------------------------------
  // Step 4 -- results
  // ------------------------------------------------------------------
  function renderResults() {
    const results = state.lastResults;
    const banner = $("#ai-error-banner");

    if (!results) {
      banner.classList.remove("hidden");
      banner.textContent = `No report available yet: ${state.lastAiError || "unknown error."}`;
      return;
    }

    if (state.lastAiError) {
      banner.classList.remove("hidden");
      banner.textContent = `API Error Detected: ${state.lastAiError}. AI evaluation unavailable — fell back to strict keyword matching.`;
    } else {
      banner.classList.add("hidden");
    }

    $("#results-role-title").textContent = `Results: ${state.lastRole}`;
    $("#results-exp-level").textContent = `Typical experience level: ${results.experience_level}`;

    $("#metric-readiness").textContent = `${results.readiness_score.toFixed(0)}%`;
    $("#metric-coverage").textContent = `${results.coverage_score.toFixed(0)}%`;
    $("#metric-strong").textContent = results.strong_matches.length;
    $("#metric-critical").textContent = results.critical_missing.length;

    $("#bar-readiness").style.width = `${results.readiness_score}%`;
    $("#bar-coverage").style.width = `${results.coverage_score}%`;

    renderGapLists(results);
    renderCharts(state.lastRole, state.lastRequiredSkills, state.lastSkillProficiency);
    renderRoadmap(results, state.lastRoadmapWeeks, state.lastRoadmapError);
  }

  function renderGapLists(results) {
    fillList("#list-strong", results.strong_matches, "None yet.");
    fillList("#list-improve", results.needs_improvement, "Nothing stuck at Beginner level.");
    fillList("#list-critical", results.critical_missing, "None. Full coverage.");
  }

  function fillList(selector, items, emptyText) {
    const el = $(selector);
    if (!items || !items.length) {
      el.textContent = emptyText;
      return;
    }
    el.innerHTML = items.map((item) => `- ${escapeHtml(item)}`).join("<br/>");
  }

  function proficiencyLabel(value) {
    const labels = { 0: "None (0%)", 0.4: "Beginner (40%)", 0.8: "Intermediate (80%)", 1: "Advanced (100%)" };
    return labels[value] !== undefined ? labels[value] : `${(value * 100).toFixed(0)}%`;
  }

  function renderCharts(selectedRole, requiredSkills, skillProficiency) {
    const categories = [];
    const userValues = [];

    (requiredSkills || []).forEach((requirement) => {
      categories.push(requirement.split("/")[0].trim());
      const options = requirement.split("/").map((o) => o.trim().toLowerCase());
      const matched = options.filter((o) => o in skillProficiency).map((o) => skillProficiency[o]);
      userValues.push(matched.length ? Math.max(...matched) : 0.0);
    });

    if (!categories.length) return;

    if (radarChart) radarChart.destroy();
    if (barChart) barChart.destroy();

    const radarCtx = $("#radar-chart").getContext("2d");
    radarChart = new Chart(radarCtx, {
      type: "radar",
      data: {
        labels: categories,
        datasets: [
          {
            label: "Role Baseline",
            data: categories.map(() => 1.0),
            borderColor: "rgba(156, 163, 175, 0.6)",
            borderDash: [5, 4],
            backgroundColor: "rgba(156, 163, 175, 0.06)",
            pointBackgroundColor: "rgba(156, 163, 175, 0.9)",
          },
          {
            label: "Your Profile",
            data: userValues,
            borderColor: "#2dd4bf",
            borderWidth: 2.5,
            backgroundColor: "rgba(45, 212, 191, 0.35)",
            pointBackgroundColor: "#2dd4bf",
            pointBorderColor: "#fff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: `Skill Profile vs. ${selectedRole} Baseline`, color: "#fafafa", font: { size: 15 } },
          legend: { labels: { color: "#e2e8f0" } },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                if (ctx.datasetIndex === 1) {
                  return `Your level: ${proficiencyLabel(userValues[ctx.dataIndex])}`;
                }
                return "Required: 100%";
              },
            },
          },
        },
        scales: {
          r: {
            min: 0,
            max: 1,
            ticks: {
              stepSize: 0.4,
              color: "#cbd5e1",
              backdropColor: "transparent",
              callback: (v) => `${Math.round(v * 100)}%`,
            },
            grid: { color: "rgba(255,255,255,0.18)" },
            angleLines: { color: "rgba(255,255,255,0.18)" },
            pointLabels: { color: "#e2e8f0", font: { size: 12 } },
          },
        },
      },
    });

    const fulfillment = userValues.map((v) => v * 100);
    const barColors = fulfillment.map((v) => (v >= 80 ? "#22c55e" : v >= 40 ? "#eab308" : "#ef4444"));

    const barCtx = $("#bar-chart").getContext("2d");
    $("#bar-chart").parentElement.style.height = `${Math.max(260, categories.length * 48)}px`;
    barChart = new Chart(barCtx, {
      type: "bar",
      data: {
        labels: categories,
        datasets: [
          {
            data: fulfillment,
            backgroundColor: barColors,
            borderRadius: 4,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.raw.toFixed(0)}% fulfilled`,
            },
          },
        },
        scales: {
          x: {
            min: 0,
            max: 100,
            ticks: { color: "#cbd5e1", callback: (v) => `${v}%` },
            grid: { color: "rgba(255,255,255,0.12)" },
            title: { display: true, text: "Fulfillment of role requirement", color: "#cbd5e1" },
          },
          y: {
            ticks: { color: "#e2e8f0" },
            grid: { display: false },
          },
        },
      },
    });
  }

  function renderRoadmap(results, roadmapWeeks, roadmapError) {
    const msgEl = $("#roadmap-message");
    const weeksEl = $("#roadmap-weeks");
    weeksEl.innerHTML = "";

    if (!results.critical_missing.length) {
      msgEl.classList.remove("hidden");
      msgEl.className = "callout callout-success";
      msgEl.textContent = "No critical missing skills detected — an AI roadmap isn't required for this role.";
      return;
    }
    if (roadmapError) {
      msgEl.classList.remove("hidden");
      msgEl.className = "callout callout-warning";
      msgEl.textContent = `AI roadmap generation is currently unavailable: ${roadmapError}`;
      return;
    }
    if (!roadmapWeeks || !roadmapWeeks.weeks || !roadmapWeeks.weeks.length) {
      msgEl.classList.remove("hidden");
      msgEl.className = "callout callout-warning";
      msgEl.textContent = "AI roadmap generation is currently unavailable. Please try again later.";
      return;
    }

    msgEl.classList.add("hidden");
    roadmapWeeks.weeks.forEach((week, wIdx) => {
      const card = document.createElement("div");
      card.className = "roadmap-week";

      const header = document.createElement("div");
      header.className = "roadmap-week-header";
      header.textContent = week.week_title;
      card.appendChild(header);

      const body = document.createElement("div");
      body.className = "roadmap-week-body";

      if (!week.tasks.length) {
        const p = document.createElement("p");
        p.className = "field-caption";
        p.textContent = "No tasks generated for this week.";
        body.appendChild(p);
      } else {
        week.tasks.forEach((task, tIdx) => {
          const row = document.createElement("div");
          row.className = "roadmap-task";
          const id = `roadmap_task_${wIdx}_${tIdx}`;

          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.id = id;
          checkbox.addEventListener("change", () => row.classList.toggle("checked", checkbox.checked));

          const label = document.createElement("label");
          label.setAttribute("for", id);
          label.innerHTML = markdownLinksToHtml(task);

          row.appendChild(checkbox);
          row.appendChild(label);
          body.appendChild(row);
        });
      }

      card.appendChild(body);
      weeksEl.appendChild(card);
    });
  }

  // ------------------------------------------------------------------
  // Step 4 -- tabs
  // ------------------------------------------------------------------
  $all(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      $all(".tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      $all(".tab-panel").forEach((p) => p.classList.add("hidden"));
      $(`#tab-${btn.dataset.tab}`).classList.remove("hidden");
    });
  });

  // ------------------------------------------------------------------
  // Step 4 -- download + reset
  // ------------------------------------------------------------------
  $("#btn-download-report").addEventListener("click", async () => {
    if (!state.lastResults) return;
    const resp = await fetch("/api/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: state.lastRole,
        results: state.lastResults,
        roadmapWeeks: state.lastRoadmapWeeks,
      }),
    });
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "SkillGap_Assessment_Report.md";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  $("#btn-start-over").addEventListener("click", resetApp);

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------
  function dedupe(arr) {
    const seen = new Set();
    const out = [];
    for (const item of arr) {
      const key = item.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        out.push(item);
      }
    }
    return out;
  }

  function splitCommaList(raw) {
    if (!raw) return [];
    return dedupe(
      raw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
    );
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function markdownLinksToHtml(text) {
    const escaped = escapeHtml(text);
    return escaped.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  }

  // ------------------------------------------------------------------
  // Init
  // ------------------------------------------------------------------
  loadCatalog().then(() => goToStep(0));
})();
