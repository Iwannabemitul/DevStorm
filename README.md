# SkillGap Intelligence

**AI-powered skill-gap and career-readiness analysis — built for the DevStorm 2026 Hackathon (Round 1).**

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B)
![AI](https://img.shields.io/badge/AI-Gemini%20%2F%20Llama%203.3-4285F4)
![Status](https://img.shields.io/badge/status-hackathon%20submission-lightgrey)

Upload a resume or hand-pick your skills, choose a target job role, and get back a readiness score, a visual skill-gap breakdown, and an AI-written 4-week roadmap for closing the gaps — all in one Streamlit app.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Supported Roles](#supported-roles)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Team](#team)
- [License](#license)

## Overview

SkillGap Intelligence answers one question for job seekers and career-switchers: **"How ready am I for this role, and what should I do next?"**

Instead of a static checklist, it uses an LLM to *semantically* compare your skills against a role's requirements — so knowing PyTorch can reasonably count toward "Machine Learning," the way a human recruiter would read a resume, rather than requiring an exact keyword match. The output is a readiness score, a categorized skill-gap breakdown, and a prioritized, project-based learning roadmap.

**Demo:** not yet deployed — run it locally with the steps in [Getting Started](#getting-started).

## Features

- **Resume skill extraction** — upload a PDF/TXT resume; an LLM call pulls out technical skills and pre-fills the picker for you.
- **37 target roles across 14 domains** — software engineering, data, AI/ML, hardware & embedded, mobile, game dev, cloud & DevOps, cybersecurity, Web3, databases, QA, product/program management, design, and marketing (full list in [Supported Roles](#supported-roles)).
- **Skill picker** with 80+ predefined technologies, plus free-text custom skills for anything not on the list.
- **Per-skill proficiency sliders** — Beginner / Intermediate / Advanced — so the score reflects depth, not just familiarity.
- **AI semantic gap analysis** — Gemini-first, Llama-3.3-via-NVIDIA-fallback scoring of Role Readiness and Skill Coverage, with every required skill bucketed into Strong Match, Needs Improvement, or Critical Missing Gap. Falls back to deterministic keyword matching if no AI provider is reachable.
- **Radar + bar chart visualizations** of your profile against the role baseline.
- **Prioritized action plan** — critical gaps first, then beginner-level skills worth strengthening.
- **AI-generated 4-week learning roadmap** for critical gaps, with every topic linked out to a YouTube search.
- **One-click Markdown report** of the full assessment, ready to download.

## How It Works

**1. Upload your resume** *(optional)* and extract skills automatically.

![Upload resume screen](screenshots/01-upload-resume.png)

**2. Pick a target role and set your skills** — from the extracted resume, the predefined list, or typed in manually.

![Target role and skill selection](screenshots/02-configure-role-skills.png)

**3. Set a proficiency level** for each skill you've selected.

![Skill proficiency sliders](screenshots/03-set-proficiency.png)

**4. Click Analyze.** The app calls the LLM to semantically score your profile, with live status as it works.

![Analysis in progress](screenshots/04-run-analysis.png)

**5. Read your results** — Role Readiness, Skill Coverage, Strong Matches, and Critical Gaps, at a glance.

![Results overview](screenshots/05-results-overview.png)

**6. Explore the Gap Analysis tab** for a radar chart of your profile against the role baseline...

![Skill profile radar chart](screenshots/06-skill-radar.png)

...and a color-coded fulfillment bar chart, with your skills sorted into Strong Matches, Needs Improvement, and Critical Missing Gaps.

![Skill fulfillment bar chart and gap columns](screenshots/07-skill-fulfillment.png)

**7. Switch to the Action Plan tab** for a prioritized breakdown of what to tackle first, an AI-written 4-week roadmap, and a one-click Markdown report download.

![Priority breakdown](screenshots/08-priority-breakdown.png)

## Tech Stack

| Layer | Tools |
|---|---|
| UI | [Streamlit](https://streamlit.io/) |
| AI / LLM | [Google Gemini](https://ai.google.dev/) (primary — auto-selects the best available model on your account), [Llama 3.3 70B via NVIDIA NIM](https://build.nvidia.com/) (fallback) |
| Charts | [Plotly](https://plotly.com/python/) (radar + bar charts) |
| Resume parsing | [PyPDF2](https://pypi.org/project/PyPDF2/) |
| Language | Python 3 |

## Project Structure

```text
DevStorm/
├── app.py              # Main Streamlit app — UI, scoring logic, charts, LLM calls
├── brain.py             # Scaffolded FastAPI microservice, not currently used by app.py
├── requirements.txt     # Pinned Python dependencies
├── .devcontainer/        # Dev container config (GitHub Codespaces)
└── .gitignore
```

> `brain.py` is an early scaffold for a separate processing service — right now it just health-checks and echoes back uppercased text — and isn't wired into `app.py` yet. All of the app's real logic (scoring, charts, LLM calls) currently lives in `app.py`.

## Getting Started

### Prerequisites

- Python 3.10+
- A [Gemini API key](https://aistudio.google.com/app/apikey) and/or an [NVIDIA NIM API key](https://build.nvidia.com/) — at least one is required for **resume skill extraction** and the **AI-generated roadmap**. The core gap analysis will still run without a key, falling back to deterministic keyword matching instead of the semantic LLM evaluation.

### Installation

```bash
git clone https://github.com/sharma-ronak75/DevStorm.git
cd DevStorm
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Create `.streamlit/secrets.toml` in the project root (already gitignored, so it's safe to put real keys here):

```toml
GEMINI_API_KEY = "your-gemini-api-key"
NVIDIA_API_KEY = "your-nvidia-api-key"   # optional fallback
```

### Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Supported Roles

<details>
<summary>37 target roles across 14 domains (click to expand)</summary>

**Core Software Engineering**
Software Engineer · Full Stack Developer · Backend Developer · Frontend Developer

**Data**
Data Scientist · Data Engineer · Data Analyst

**AI / Machine Learning**
AI Engineer · Machine Learning Engineer · MLOps Engineer · NLP Engineer · Computer Vision Engineer · Robotics Engineer

**Hardware & Systems**
Embedded Systems Engineer · IoT Architect · Firmware Engineer · Hardware Design Engineer · Systems Optimization Engineer

**Mobile**
Android Developer · iOS Developer

**Game Development**
Game Developer · Game Designer

**Cloud & Infrastructure**
Cloud Architect · DevOps Engineer · Site Reliability Engineer

**Cybersecurity**
Cybersecurity Analyst · Penetration Tester · Security Engineer

**Web3 / Blockchain**
Blockchain Developer · Web3 Engineer

**Databases**
Database Administrator · Database Engineer

**QA**
QA Automation Engineer

**Product & Program Management**
Product Manager · Technical Program Manager

**Design**
UX/UI Designer

**Marketing**
Digital Marketing Specialist

Each role has its own curated list of required skills and a typical experience level, defined in `app.py`.

</details>

## Roadmap

Ideas for Round 2 and beyond:

- Wire `brain.py` up as a real backend service instead of a stub
- Persist assessment history — everything currently lives in Streamlit's session state and resets on refresh
- Let users define custom roles and required-skill sets
- Add lightweight auth so proficiency data survives across sessions

## Contributing

This started as a hackathon submission, but issues and PRs are welcome — bug fixes, new roles/skills, or UI polish are all fair game. Fork the repo, make your changes, and open a pull request.

## Team

Built by [@sharma-ronak75](https://github.com/sharma-ronak75) for the DevStorm 2026 Hackathon. This repository is a fork of the team's original submission at [Iwannabemitul/DevStorm](https://github.com/Iwannabemitul/DevStorm).

## License

No license file is currently included in this repository. Until one is added, all rights are reserved by the authors — reach out before reusing this code outside the hackathon.
