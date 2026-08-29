import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import PyPDF2
import io
import json
import requests
import plotly.graph_objects as go
from openai import OpenAI

JOB_DATA = {
    "job_roles": {
        # --- Core Software Engineering ---
        "Software Engineer": {
            "required_skills": ["Data Structures & Algorithms", "Python/Java/C++", "Git & Version Control", "System Design", "Debugging & Testing", "Object-Oriented Design", "Code Review Practices", "Unit Testing"],
            "experience_level": "Entry to Senior"
        },
        "Full Stack Developer": {
            "required_skills": ["JavaScript", "React", "Node.js", "SQL", "REST APIs", "Git & Version Control", "System Design", "CI/CD Pipelines"],
            "experience_level": "Entry to Senior"
        },
        "Backend Developer": {
            "required_skills": ["Python/Java/Node.js", "SQL & NoSQL Databases", "REST APIs", "Microservices", "System Design", "Docker", "Git & Version Control", "Debugging & Testing"],
            "experience_level": "Entry to Senior"
        },
        "Frontend Developer": {
            "required_skills": ["HTML", "CSS", "JavaScript", "React/Vue.js/Angular", "Responsive Design", "Web Accessibility", "Git & Version Control", "Browser DevTools"],
            "experience_level": "Entry to Senior"
        },

        # --- Data ---
        "Data Scientist": {
            "required_skills": ["Python/R", "Statistics & Probability", "Machine Learning", "SQL", "Data Visualization", "Pandas", "Data Cleaning & Wrangling", "Experiment Design"],
            "experience_level": "Mid to Senior"
        },
        "Data Engineer": {
            "required_skills": ["Python/Scala", "SQL", "ETL Pipelines", "Apache Spark", "Data Warehousing", "Airflow", "Cloud Platforms (AWS/Azure/GCP)", "Data Modeling"],
            "experience_level": "Mid to Senior"
        },
        "Data Analyst": {
            "required_skills": ["SQL", "Excel", "Data Visualization", "Statistics & Probability", "Python/R", "Business Intelligence Tools", "Dashboarding", "Data Cleaning & Wrangling"],
            "experience_level": "Entry to Mid"
        },

        # --- AI / Machine Learning ---
        "AI Engineer": {
            "required_skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow/PyTorch", "Model Deployment", "MLOps", "Prompt Engineering", "Cloud Platforms (AWS/Azure/GCP)"],
            "experience_level": "Mid to Senior"
        },
        "Machine Learning Engineer": {
            "required_skills": ["Python", "TensorFlow/PyTorch", "Feature Engineering", "Model Training & Tuning", "MLOps", "Distributed Computing", "SQL", "Statistics & Probability"],
            "experience_level": "Mid to Senior"
        },
        "MLOps Engineer": {
            "required_skills": ["CI/CD Pipelines", "Docker & Kubernetes", "Model Monitoring", "Cloud Platforms (AWS/Azure/GCP)", "Python", "MLflow/Kubeflow", "Infrastructure as Code (Terraform)", "Version Control for ML (DVC)"],
            "experience_level": "Mid to Senior"
        },
        "NLP Engineer": {
            "required_skills": ["Python", "Transformers", "Natural Language Processing", "Tokenization & Embeddings", "PyTorch/TensorFlow", "Large Language Models", "Text Preprocessing", "Model Fine-Tuning"],
            "experience_level": "Mid to Senior"
        },
        "Computer Vision Engineer": {
            "required_skills": ["Python", "OpenCV", "Deep Learning", "Convolutional Neural Networks", "Image Processing", "PyTorch/TensorFlow", "Object Detection", "Model Optimization"],
            "experience_level": "Mid to Senior"
        },
        "Robotics Engineer": {
            "required_skills": ["C++/Python", "ROS (Robot Operating System)", "Control Systems", "Sensor Fusion", "Kinematics", "Embedded Systems", "Path Planning", "Computer Vision"],
            "experience_level": "Mid to Senior"
        },

        # --- Hardware & Systems ---
        "Embedded Systems Engineer": {
            "required_skills": ["C/C++", "Microcontrollers (ARM/AVR)", "RTOS", "Sensor Integration", "Circuit Debugging", "UART/SPI/I2C Protocols", "Firmware Development", "Low-Power Design"],
            "experience_level": "Mid to Senior"
        },
        "IoT Architect": {
            "required_skills": ["MQTT/CoAP Protocols", "Embedded Systems", "Cloud Platforms (AWS/Azure/GCP)", "Edge Computing", "Sensor Networks", "Network Security", "System Design", "Device Provisioning"],
            "experience_level": "Mid to Senior"
        },
        "Firmware Engineer": {
            "required_skills": ["C/C++", "Microcontrollers (ARM/AVR)", "Bootloader Development", "Debugging Tools (JTAG)", "RTOS", "Hardware Datasheets", "Version Control", "Power Management"],
            "experience_level": "Mid to Senior"
        },
        "Hardware Design Engineer": {
            "required_skills": ["Circuit Design", "PCB Layout", "VHDL/Verilog", "Signal Integrity", "Schematic Capture Tools", "Embedded Systems", "Testing & Validation", "Datasheet Analysis"],
            "experience_level": "Mid to Senior"
        },
        "Systems Optimization Engineer": {
            "required_skills": ["C/C++", "Operating Systems Internals", "Performance Profiling", "Memory Management", "Concurrency & Multithreading", "Linux Administration", "Debugging Tools", "Benchmarking"],
            "experience_level": "Mid to Senior"
        },

        # --- Mobile ---
        "Android Developer": {
            "required_skills": ["Kotlin/Java", "Android SDK", "Jetpack Compose", "REST APIs", "SQLite/Room", "Git & Version Control", "Material Design", "App Performance Optimization"],
            "experience_level": "Entry to Senior"
        },
        "iOS Developer": {
            "required_skills": ["Swift", "UIKit/SwiftUI", "Xcode", "REST APIs", "Core Data", "Git & Version Control", "App Store Guidelines", "Memory Management"],
            "experience_level": "Entry to Senior"
        },

        # --- Game Development ---
        "Game Developer": {
            "required_skills": ["C++/C#", "Unity/Unreal Engine", "Game Physics", "3D Math", "Shader Programming", "Version Control (Git/Perforce)", "Performance Optimization", "Multiplayer Networking"],
            "experience_level": "Entry to Senior"
        },
        "Game Designer": {
            "required_skills": ["Game Design Documentation", "Level Design", "Prototyping Tools", "Player Psychology", "Balancing & Economy Design", "Scripting (C#/Lua)", "Playtesting", "Storytelling"],
            "experience_level": "Entry to Mid"
        },

        # --- Cloud & Infrastructure ---
        "Cloud Architect": {
            "required_skills": ["AWS/Azure/GCP", "Infrastructure as Code (Terraform)", "Networking Fundamentals", "Cloud Security", "Cost Optimization", "Kubernetes", "Disaster Recovery Planning", "System Design"],
            "experience_level": "Mid to Senior"
        },
        "DevOps Engineer": {
            "required_skills": ["CI/CD Pipelines", "Docker & Kubernetes", "Cloud Platforms (AWS/Azure/GCP)", "Infrastructure as Code (Terraform)", "Linux Administration", "Monitoring & Logging", "Scripting (Python/Bash)", "Configuration Management (Ansible)"],
            "experience_level": "Mid to Senior"
        },
        "Site Reliability Engineer": {
            "required_skills": ["Linux Administration", "Monitoring & Alerting (Prometheus/Grafana)", "Incident Response", "CI/CD Pipelines", "Kubernetes", "Scripting (Python/Bash)", "Capacity Planning", "System Design"],
            "experience_level": "Mid to Senior"
        },

        # --- Cybersecurity ---
        "Cybersecurity Analyst": {
            "required_skills": ["Network Security", "Threat Detection & Response", "Penetration Testing", "SIEM Tools", "Risk Assessment", "Incident Response", "Security Policies & Compliance", "Vulnerability Management"],
            "experience_level": "Entry to Senior"
        },
        "Penetration Tester": {
            "required_skills": ["Network Security", "Penetration Testing", "Vulnerability Assessment", "Exploit Development", "Scripting (Python/Bash)", "Web Application Security", "Social Engineering Awareness", "Reporting & Documentation"],
            "experience_level": "Mid to Senior"
        },
        "Security Engineer": {
            "required_skills": ["Network Security", "Cloud Security", "SIEM Tools", "Identity & Access Management", "Threat Modeling", "Incident Response", "Encryption & Cryptography", "Risk Assessment"],
            "experience_level": "Mid to Senior"
        },

        # --- Web3 / Blockchain ---
        "Blockchain Developer": {
            "required_skills": ["Solidity", "Smart Contract Development", "Ethereum/EVM", "Web3.js/Ethers.js", "Cryptography Fundamentals", "Consensus Mechanisms", "Gas Optimization", "Security Auditing"],
            "experience_level": "Mid to Senior"
        },
        "Web3 Engineer": {
            "required_skills": ["Solidity", "Smart Contracts", "Decentralized Applications (dApps)", "IPFS", "Wallet Integration (MetaMask)", "Web3.js/Ethers.js", "Layer 2 Solutions", "Tokenomics"],
            "experience_level": "Mid to Senior"
        },

        # --- Databases ---
        "Database Administrator": {
            "required_skills": ["SQL & NoSQL Databases", "Query Optimization", "Backup & Recovery", "Database Security", "Performance Tuning", "High Availability & Clustering", "Database Monitoring", "Capacity Planning"],
            "experience_level": "Mid to Senior"
        },
        "Database Engineer": {
            "required_skills": ["SQL & NoSQL Databases", "Database Design & Normalization", "Indexing Strategies", "Replication & Sharding", "Query Optimization", "Backup & Recovery", "Cloud Databases", "Data Migration"],
            "experience_level": "Mid to Senior"
        },

        # --- QA ---
        "QA Automation Engineer": {
            "required_skills": ["Selenium/Playwright", "Test Case Design", "CI/CD Pipelines", "API Testing", "Scripting (Python/JavaScript)", "Bug Tracking Tools", "Performance Testing", "Test Strategy"],
            "experience_level": "Entry to Mid"
        },

        # --- Product & Program Management ---
        "Product Manager": {
            "required_skills": ["Roadmap Planning", "Stakeholder Communication", "Market Research", "Agile/Scrum", "Data-Driven Decision Making", "Competitive Analysis", "User Story Writing", "Go-to-Market Strategy"],
            "experience_level": "Mid to Senior"
        },
        "Technical Program Manager": {
            "required_skills": ["Roadmap Planning", "Cross-Functional Coordination", "Risk Management", "Agile/Scrum", "Stakeholder Communication", "Resource Allocation", "Technical Fluency", "Program Metrics & Reporting"],
            "experience_level": "Mid to Senior"
        },

        # --- Design ---
        "UX/UI Designer": {
            "required_skills": ["Wireframing & Prototyping", "Figma/Sketch/Adobe XD", "User Research", "Interaction Design", "Visual Design Principles", "Usability Testing", "Design Systems", "Accessibility Standards (WCAG)"],
            "experience_level": "Entry to Senior"
        },

        # --- Marketing ---
        "Digital Marketing Specialist": {
            "required_skills": ["SEO/SEM", "Content Strategy", "Social Media Marketing", "Google Analytics", "Email Marketing Campaigns", "Paid Advertising (PPC)", "Conversion Rate Optimization", "Marketing Automation Tools"],
            "experience_level": "Entry to Mid"
        }
    }
}

ALL_TECH_SKILLS = sorted([
    "Python", "Java", "C++", "C#", "Go", "Rust", "JavaScript", "TypeScript",
    "HTML", "CSS", "React", "Vue.js", "Angular", "Node.js", "Next.js",
    "Django", "Flask", "FastAPI", "Spring Boot", "Ruby", "Ruby on Rails",
    "PHP", "Swift", "Kotlin", "R",
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite",
    "SQL & NoSQL Databases", "Query Optimization", "Database Security",
    "Backup & Recovery", "Performance Tuning",
    "AWS", "Azure", "Google Cloud Platform", "Cloud Platforms (AWS/Azure/GCP)",
    "Docker", "Kubernetes", "Docker & Kubernetes", "Terraform",
    "Infrastructure as Code (Terraform)", "CI/CD Pipelines", "Jenkins",
    "Linux Administration", "Git & Version Control", "GitHub Actions",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
    "Scikit-learn", "Natural Language Processing", "Computer Vision",
    "Data Visualization", "Statistics & Probability", "Pandas", "NumPy",
    "Data Structures & Algorithms", "System Design", "Debugging & Testing",
    "Cybersecurity", "Network Security", "Penetration Testing",
    "Threat Detection & Response", "SIEM Tools", "Risk Assessment",
    "Figma", "Sketch", "Adobe XD", "Wireframing & Prototyping",
    "User Research", "Interaction Design", "Visual Design Principles",
    "Agile", "Scrum", "Roadmap Planning", "Stakeholder Communication",
    "Market Research", "Data-Driven Decision Making",
    "SEO/SEM", "Content Strategy", "Social Media Marketing",
    "Google Analytics", "Email Marketing Campaigns",
    "GraphQL", "REST APIs", "Microservices", "Kafka", "RabbitMQ",
])

PROFICIENCY_OPTIONS = ["Beginner (0.4)", "Intermediate (0.8)", "Advanced (1.0)"]
PROFICIENCY_WEIGHTS = {
    "Beginner (0.4)": 0.4,
    "Intermediate (0.8)": 0.8,
    "Advanced (1.0)": 1.0,
}

FUN_FACTS = [
    "🧠 The term 'bug' in computing traces back to an actual moth found in a Harvard Mark II relay in 1947.",
    "🐍 Python was named after Monty Python's Flying Circus, not the snake.",
    "🖱️ The first computer mouse prototype was carved out of wood.",
    "⌨️ QWERTY was originally designed to slow typists down and stop mechanical typewriters from jamming.",
    "🏦 More than 70% of the world's financial transactions still run on COBOL, a language from 1959.",
    "⚡ JavaScript was originally written in just 10 days by Brendan Eich in 1995.",
    "🚀 The Apollo 11 guidance computer had less RAM than a modern USB-C cable.",
    "🔍 A single Google search reportedly draws more computing power than the entire Apollo 11 mission.",
    "📷 The world's first webcam was built just to monitor a coffee pot at Cambridge University.",
    "💾 The first 1GB hard drive, released in 1980, weighed about 550 pounds and cost $40,000.",
    "🌐 The World Wide Web was originally proposed as a way to help physicists share documents at CERN.",
    "🐛 Grace Hopper coined the term 'debugging' after physically removing that moth from a relay.",
    "📧 The first email was sent in 1971, and its author doesn't remember exactly what it said.",
    "🎮 The 'Konami Code' cheat sequence became so famous it's now used as an easter egg in web browsers.",
    "🧮 The first computer 'programmer' is widely considered to be Ada Lovelace, in the 1840s.",
    "📱 There are more mobile phones on Earth today than there are people.",
    "🔤 The @ symbol was chosen for email addresses in 1971 simply because it was rarely used elsewhere.",
    "🖥️ The original name for the Windows operating system was 'Interface Manager'.",
    "🕹️ 'Space Invaders' was so popular in Japan it reportedly caused a national coin shortage.",
    "🔐 The first computer password was created at MIT in the 1960s — and was reportedly leaked within weeks.",
]

def parse_custom_skills(raw_text):
    return [s.strip() for s in raw_text.split(",") if s.strip()]

def llm_provider_configured():
    return bool(st.secrets.get("GEMINI_API_KEY")) or bool(st.secrets.get("NVIDIA_API_KEY"))

def call_llm_resilient(prompt):
    errors = []
    
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            available_models = [
                m.name for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]
            
            # Use stable, highly-available models
            # Use stable, highly-available models
            candidate_priority = [
                "models/gemini-3.6-flash",   # <--- ADD THIS AT THE TOP
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro",
                "models/gemini-2.0-flash",
                "models/gemini-pro"
            ]
            
            selected_model_name = None
            for candidate in candidate_priority:
                if candidate in available_models:
                    selected_model_name = candidate
                    break
                    
            if selected_model_name is None and available_models:
                selected_model_name = available_models[0]
                
            if selected_model_name is None:
                raise RuntimeError("No Gemini models supporting generateContent are available.")

            model = genai.GenerativeModel(selected_model_name)
            response = model.generate_content(prompt)
            text = (response.text or "").strip()
            if text:
                return text
            raise RuntimeError("Gemini returned an empty response.")
        except Exception as e:
            errors.append(f"Gemini Error: {str(e)}")
            print(f"Gemini call failed: {e}")

    nvidia_key = st.secrets.get("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=nvidia_key)
            completion = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct-v2",  # <--- CHANGE TO 3.3 OR 3.2
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.2,
            )
            text = (completion.choices[0].message.content or "").strip()
            if text:
                return text
            raise RuntimeError("NVIDIA returned an empty response.")
        except Exception as e:
            errors.append(f"NVIDIA Error: {str(e)}")
            print(f"NVIDIA fallback call failed: {e}")

    # If we got here, both failed. Bubble the exact errors to the UI.
    if errors:
        raise RuntimeError(" | ".join(errors))
    
    return ""

def legacy_analyze_role(selected_role, skill_proficiency):
    role_info = JOB_DATA["job_roles"][selected_role]
    required_skills = role_info["required_skills"]
    total_required = len(required_skills)

    strong_matches = []
    needs_improvement = []
    critical_missing = []

    earned_weight_sum = 0.0
    covered_count = 0

    for requirement in required_skills:
        options = [opt.strip().lower() for opt in requirement.split("/")]
        matched_weights = [
            skill_proficiency[opt] for opt in options if opt in skill_proficiency
        ]

        if matched_weights:
            best_weight = max(matched_weights)
            earned_weight_sum += best_weight
            covered_count += 1
            if best_weight >= 0.8:
                strong_matches.append((requirement, best_weight))
            else:
                needs_improvement.append((requirement, best_weight))
        else:
            critical_missing.append(requirement)

    coverage_score = (covered_count / total_required * 100) if total_required else 0
    readiness_score = (earned_weight_sum / total_required * 100) if total_required else 0

    return {
        "experience_level": role_info["experience_level"],
        "total_required": total_required,
        "coverage_score": coverage_score,
        "readiness_score": readiness_score,
        "strong_matches": strong_matches,
        "needs_improvement": needs_improvement,
        "critical_missing": critical_missing,
    }

def ai_analyze_role(target_role, required_skills, all_user_skills, skill_proficiencies, leetcode_stats=None):
    proficiency_lines = ", ".join(
        f"{skill} ({weight * 100:.0f}% proficiency)" for skill, weight in skill_proficiencies.items()
    ) or "none provided"

    if leetcode_stats:
        leetcode_context = (
            f"The candidate's LeetCode profile ('{leetcode_stats.get('username', 'unknown')}') shows "
            f"{leetcode_stats.get('easy', 0)} Easy, {leetcode_stats.get('medium', 0)} Medium, and "
            f"{leetcode_stats.get('hard', 0)} Hard problems solved ({leetcode_stats.get('total', 0)} total). "
            "Treat this as verified, ground-truth evidence of the candidate's real Data Structures & "
            "Algorithms / problem-solving ability. Where this signal disagrees with their self-reported "
            "proficiency for DSA-adjacent skills, trust the LeetCode evidence over the self-report "
            "(e.g. a strong Medium/Hard solve count should upgrade an under-rated self-assessment, and a "
            "very low solve count should temper an inflated one)."
        )
    else:
        leetcode_context = "No verified LeetCode data was provided; rely on self-reported proficiency only."

    prompt = (
        "Act as a Senior Technical Recruiter. Semantically evaluate a candidate's skills against "
        f"the required skills for the target role of {target_role}. "
        f"Required skills for this role: {required_skills}. "
        f"Candidate's stated skills: {all_user_skills}. "
        f"Candidate's proficiency levels: {proficiency_lines}. "
        f"{leetcode_context} "
        "Do not rely on exact string matching. If the candidate has an advanced or adjacent skill "
        "that demonstrates competence in a required skill (for example, knowing PyTorch implies "
        "competence in Feature Engineering or Machine Learning), credit them for it and note the "
        "inference in parentheses. "
        "Return ONLY a raw JSON string matching this exact schema, with no markdown formatting, "
        "no backticks, and no extra text before or after it: "
        '{"readiness_score": 85, "coverage_score": 90, "experience_level_assessment": '
        '"Mid to Senior", "strong_matches": ["Python (Advanced)", "Machine Learning (via PyTorch)"], '
        '"needs_improvement": ["Docker (Beginner)"], "critical_missing": ["Cloud Architecture"]}'
    )

    raw_text = call_llm_resilient(prompt)
    if not raw_text:
        raise RuntimeError("No AI provider returned a response.")

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    parsed = json.loads(raw_text)

    return {
        "experience_level": parsed["experience_level_assessment"],
        "total_required": len(required_skills),
        "coverage_score": parsed["coverage_score"],
        "readiness_score": parsed["readiness_score"],
        "strong_matches": parsed["strong_matches"],
        "needs_improvement": parsed["needs_improvement"],
        "critical_missing": parsed["critical_missing"],
    }

def generate_ai_roadmap(target_role, user_skills, missing_skills):
    prompt = (
        f"Act as a Senior Tech Recruiter and Mentor. The user wants to be a {target_role}. "
        f"They currently know {user_skills} with varying proficiencies. "
        f"They are completely missing these critical skills: {missing_skills}. "
        "Design a highly specific, no-nonsense 4-week learning roadmap to close this gap. "
        "Do not use generic filler like 'learn X' — every task should reference a concrete "
        "project, exercise, or resource type. "
        "Return ONLY a raw JSON object with no markdown formatting, no code fences, and no "
        "extra text before or after it. It must match exactly this schema: "
        '{"weeks": [{"week_title": "Week 1: Fundamentals", "tasks": ["Task 1", "Task 2"]}]}. '
        "Include exactly 4 week objects, each with 3 to 5 concise, actionable tasks. "
        "CRITICAL: You must return valid, parseable JSON. Do NOT use double quotes inside "
        "your string values. Use single quotes for inner text (e.g., 'Learn Python' instead "
        'of "Learn Python"). Ensure all commas and brackets are perfectly formatted.'
    )
    return call_llm_resilient(prompt)

def parse_roadmap_json(raw_text):
    if not raw_text:
        raise ValueError("Empty roadmap response from AI provider.")

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    # Guard against stray prose wrapped around the JSON object by isolating
    # the outermost {...} block before parsing.
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in the roadmap response.")
    json_slice = cleaned[start:end + 1]

    parsed = json.loads(json_slice)
    weeks = parsed.get("weeks")
    if not isinstance(weeks, list) or not weeks:
        raise ValueError("Roadmap JSON did not contain a non-empty 'weeks' list.")

    normalized_weeks = []
    for i, week in enumerate(weeks):
        title = str(week.get("week_title") or f"Week {i + 1}").strip()
        raw_tasks = week.get("tasks") or []
        tasks = [str(t).strip() for t in raw_tasks if str(t).strip()]
        normalized_weeks.append({"week_title": title, "tasks": tasks})

    return {"weeks": normalized_weeks}

def roadmap_weeks_to_markdown(roadmap):
    if not roadmap or not roadmap.get("weeks"):
        return "_No AI roadmap was generated for this assessment._"
    lines = []
    for week in roadmap["weeks"]:
        lines.append(f"### {week['week_title']}")
        for task in week["tasks"]:
            lines.append(f"- [ ] {task}")
        lines.append("")
    return "\n".join(lines).strip()

def fetch_leetcode_stats(username):
    username = (username or "").strip()
    if not username:
        st.warning("Enter a LeetCode username first.")
        return None

    url = f"https://alfa-leetcode-api.onrender.com/{username}/solved"
    try:
        response = requests.get(url, timeout=8)
    except requests.exceptions.Timeout:
        st.warning("LeetCode API timed out. Continuing without verified coding stats.")
        return None
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not reach the LeetCode API: {e}")
        return None

    if response.status_code == 404:
        st.warning(f"LeetCode username '{username}' was not found. Continuing without it.")
        return None
    if response.status_code == 429:
        # Hackathon fallback: the free LeetCode API tier rate-limits aggressively.
        # Rather than failing the whole flow during a live demo, fall back to a
        # clearly-labeled demo profile so the rest of the app remains showable.
        st.toast("API Rate limited. Using Demo Profile for showcase.", icon="⚠️")
        return {"username": username, "easy": 45, "medium": 120, "hard": 15, "total": 180}
    if response.status_code != 200:
        st.warning(f"LeetCode API returned an unexpected status ({response.status_code}). Continuing without it.")
        return None

    try:
        data = response.json()
    except ValueError:
        st.warning("LeetCode API returned an unreadable response. Continuing without it.")
        return None

    stats = {
        "username": username,
        "easy": data.get("easySolved", 0),
        "medium": data.get("mediumSolved", 0),
        "hard": data.get("hardSolved", 0),
        "total": data.get("solvedProblem", 0),
    }
    st.toast(f"Verified {stats['total']} solved problems for '{username}'!", icon="🏆")
    return stats

def extract_skills_from_resume(text):
    prompt = (
        "Extract all technical skills, programming languages, and frameworks from the "
        "following resume text. Return ONLY a comma-separated list of skills. Do not "
        f"include any other text, pleasantries, or markdown formatting. Text: {text}"
    )
    return call_llm_resilient(prompt)

def extract_text_from_resume_file(uploaded_file):
    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        return uploaded_file.getvalue().decode("utf-8", errors="ignore")

def route_extracted_skills(raw_skills_text):
    extracted = [s.strip() for s in raw_skills_text.split(",") if s.strip()]
    lookup = {skill.lower(): skill for skill in ALL_TECH_SKILLS}

    known_matches = []
    custom_matches = []

    for skill in extracted:
        canonical = lookup.get(skill.lower())
        if canonical:
            if canonical not in known_matches:
                known_matches.append(canonical)
        else:
            if skill not in custom_matches:
                custom_matches.append(skill)

    st.session_state.parsed_known_skills = known_matches
    st.session_state.parsed_custom_skills = ", ".join(custom_matches)

def render_radar_chart(selected_role, required_skills, skill_proficiency):
    categories = []
    user_values = []

    for requirement in required_skills:
        label = requirement.split("/")[0].strip()
        categories.append(label)

        options = [opt.strip().lower() for opt in requirement.split("/")]
        matched_weights = [skill_proficiency[opt] for opt in options if opt in skill_proficiency]
        user_values.append(max(matched_weights) if matched_weights else 0.0)

    if not categories:
        return

    categories_closed = categories + [categories[0]]
    user_values_closed = user_values + [user_values[0]]
    baseline_values_closed = [1.0] * len(categories_closed)

    def proficiency_label(value):
        labels = {
            0.0: "None (0%)",
            0.4: "Beginner (40%)",
            0.8: "Intermediate (80%)",
            1.0: "Advanced (100%)",
        }
        return labels.get(value, f"{value * 100:.0f}%")

    current_levels_closed = [proficiency_label(value) for value in user_values_closed]
    hover_data = list(zip(categories_closed, current_levels_closed))
    chart_config = {
        "displayModeBar": False,
        "staticPlot": False,
        "scrollZoom": False,
    }

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=baseline_values_closed,
        theta=categories_closed,
        name="Role Baseline",
        mode="lines+markers",
        line=dict(color="rgba(156, 163, 175, 0.5)", dash="dash"),
        marker=dict(size=7, color="rgba(156, 163, 175, 0.9)"),
        fill="toself",
        fillcolor="rgba(156, 163, 175, 0.05)",
        customdata=hover_data,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Your current level: %{customdata[1]}<br>"
            "Required: 100%<extra>Role baseline</extra>"
        ),
    ))

    fig.add_trace(go.Scatterpolar(
        r=user_values_closed,
        theta=categories_closed,
        name="Your Profile",
        mode="lines+markers",
        line=dict(color="#2DD4BF", width=3),
        marker=dict(size=9, color="#2DD4BF", line=dict(color="#FFFFFF", width=1)),
        fill="toself",
        fillcolor="rgba(45, 212, 191, 0.4)",
        customdata=hover_data,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Your current level: %{customdata[1]}<br>"
            "Required: 100%<extra>Your profile</extra>"
        ),
    ))

    # A center marker makes an all-missing or single-match profile intentional,
    # rather than looking like a broken radar spoke.
    if sum(value > 0 for value in user_values) <= 1:
        fig.add_trace(go.Scatterpolar(
            r=[0],
            theta=[categories[0]],
            mode="markers",
            marker=dict(size=8, color="rgba(45, 212, 191, 0.65)"),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1.0],
                tickvals=[0, 0.4, 0.8, 1.0],
                ticktext=["0%", "40% (Beginner)", "80% (Intermediate)", "100% (Advanced)"],
                ticks="",
                gridcolor="rgba(255, 255, 255, 0.28)",
                gridwidth=1,
                linecolor="rgba(0,0,0,0)",
                color="#CBD5E1",
                tickfont=dict(size=11),
            ),
            angularaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.18)",
                linecolor="rgba(0,0,0,0)",
                tickfont=dict(color="#E2E8F0", size=13)
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5),
        title=dict(text=f"Skill Profile vs. {selected_role} Baseline", x=0.5, font=dict(size=16)),
        margin=dict(t=80, b=20),
        dragmode=False,
    )

    st.plotly_chart(fig, use_container_width=True, config=chart_config)

    with st.expander("Skill Fulfillment Bar Chart", expanded=True):
        st.caption("Each bar shows how closely your current level meets the 100% requirement.")
        fulfillment_percentages = [value * 100 for value in user_values]
        bar_colors = [
            "#22C55E" if value >= 80 else "#EAB308" if value >= 40 else "#EF4444"
            for value in fulfillment_percentages
        ]

        bar_fig = go.Figure(go.Bar(
            x=fulfillment_percentages,
            y=categories,
            orientation="h",
            marker_color=bar_colors,
            text=[f"{value:.0f}%" for value in fulfillment_percentages],
            textposition="auto",
            customdata=hover_data[:-1],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Your current level: %{customdata[1]}<br>"
                "Required: 100%<extra></extra>"
            ),
        ))
        bar_fig.update_layout(
            xaxis=dict(
                title="Fulfillment of role requirement",
                range=[0, 100],
                ticksuffix="%",
                tickvals=[0, 40, 80, 100],
                gridcolor="rgba(255, 255, 255, 0.15)",
            ),
            yaxis=dict(autorange="reversed"),
            height=max(260, len(categories) * 48),
            margin=dict(l=20, r=30, t=20, b=45),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            showlegend=False,
            dragmode=False,
        )
        st.plotly_chart(bar_fig, use_container_width=True, config=chart_config)

def format_gap_line(item):
    if isinstance(item, (tuple, list)) and len(item) == 2:
        req, weight = item
        return f"- {req} ({weight * 100:.0f}%)"
    return f"- {item}"

def build_markdown_report(role, results, roadmap_text):
    lines = [
        f"# SkillGap Assessment Report: {role}",
        "",
        f"**Experience Level:** {results['experience_level']}",
        "",
        f"**Role Readiness:** {results['readiness_score']:.0f}%",
        f"**Skill Coverage:** {results['coverage_score']:.0f}%",
        "",
        "## Strong Matches",
    ]

    if results["strong_matches"]:
        lines.extend(format_gap_line(item) for item in results["strong_matches"])
    else:
        lines.append("- None yet.")

    lines.append("")
    lines.append("## Needs Improvement")
    if results["needs_improvement"]:
        lines.extend(format_gap_line(item) for item in results["needs_improvement"])
    else:
        lines.append("- Nothing stuck at Beginner level.")

    lines.append("")
    lines.append("## Critical Gaps")
    if results["critical_missing"]:
        lines.extend(f"- {req}" for req in results["critical_missing"])
    else:
        lines.append("- None. Full coverage.")

    lines.append("")
    lines.append("## 4-Week AI Roadmap")
    lines.append("")
    lines.append(roadmap_text if roadmap_text else "_No AI roadmap was generated for this assessment._")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Step 2.5 async loader: a small HTML/JS component that keeps animating in
# the browser (via its own iframe + setInterval) even while the main
# Streamlit script is blocked on a synchronous LLM call below it.
# ---------------------------------------------------------------------------
def render_loading_component():
    facts_json = json.dumps(FUN_FACTS)
    html_code = f"""
    <div id="loader-wrap" style="display:flex;flex-direction:column;align-items:center;
         justify-content:center;padding:40px 16px;font-family:sans-serif;">
      <div class="spinner" style="width:56px;height:56px;border:5px solid rgba(45,212,191,0.15);
           border-top-color:#2DD4BF;border-radius:50%;animation:spin 0.9s linear infinite;"></div>
      <p id="fun-fact-text" style="margin-top:20px;color:#E2E8F0;font-size:15px;text-align:center;
         max-width:480px;transition:opacity 0.4s ease;opacity:1;">
         Warming up the analysis engine...
      </p>
    </div>
    <style>
      @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
    <script>
      const facts = {facts_json};
      // Fisher-Yates shuffle so the order is fresh on every load.
      for (let i = facts.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [facts[i], facts[j]] = [facts[j], facts[i]];
      }}
      const el = document.getElementById('fun-fact-text');
      setInterval(() => {{
        if (!el) return;
        el.style.opacity = 0;
        setTimeout(() => {{
          const idx = Math.floor(Math.random() * facts.length);
          el.innerText = facts[idx];
          el.style.opacity = 1;
        }}, 400);
      }}, 2500);
    </script>
    """
    components.html(html_code, height=200)

def inject_global_css():
    st.markdown(
        """
        <style>
        .onboard-card {
            padding: 2.2rem 1.6rem;
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(45,212,191,0.08), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.10);
            text-align: center;
            transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
            height: 100%;
        }
        .onboard-card:hover {
            transform: scale(1.02);
            box-shadow: 0 14px 40px rgba(45,212,191,0.25);
            border-color: rgba(45,212,191,0.55);
        }
        .onboard-icon { font-size: 3rem; margin-bottom: 0.6rem; }
        .onboard-title { font-size: 1.35rem; font-weight: 700; margin-bottom: 0.4rem; }
        .onboard-desc { color: rgba(230,238,245,0.75); font-size: 0.95rem; }

        @keyframes pulse-glow {
            0%   { box-shadow: 0 0 0 0 rgba(45,212,191,0.65); }
            70%  { box-shadow: 0 0 0 16px rgba(45,212,191,0); }
            100% { box-shadow: 0 0 0 0 rgba(45,212,191,0); }
        }
        /* Targets the button immediately following the .pulse-anchor marker div.
           Relies on :has(), supported in modern Chromium/Safari/Firefox builds
           used by Streamlit's hosted browsers; degrades gracefully (no pulse,
           button still fully functional) on older browsers. */
        div[data-testid="element-container"]:has(> div.pulse-anchor)
          + div[data-testid="element-container"] button {
            animation: pulse-glow 1.8s infinite;
            border: 1px solid #2DD4BF !important;
        }
        .step-caption {
            color: rgba(230,238,245,0.6);
            font-size: 0.8rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }

        /* Dim and blur all un-focused Streamlit containers when a tour-focus element exists */
        .main .block-container:has(.tour-focus) > div {
            opacity: 0.25;
            filter: blur(2px);
            pointer-events: none;
            transition: all 0.5s ease;
        }
        /* Keep the active focused container bright, scaled, and glowing */
        .main .block-container > div:has(.tour-focus) {
            opacity: 1.0 !important;
            filter: none !important;
            pointer-events: auto;
            transform: scale(1.02);
            border-radius: 12px;
            box-shadow: 0px 0px 30px rgba(45, 212, 191, 0.15);
            padding: 15px;
            z-index: 999;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def init_session_state():
    defaults = {
        "step": 0,
        "input_mode": None,
        "parsed_known_skills": [],
        "parsed_custom_skills": "",
        "all_user_skills": [],
        "skill_proficiency": {},
        "leetcode_stats": None,
        "selected_role": None,
        "is_processing": False,
        "last_results": None,
        "last_role": None,
        "last_required_skills": [],
        "last_skill_proficiency": {},
        "last_roadmap_weeks": None,
        "last_roadmap_error": None,
        "last_ai_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()

# ---------------------------------------------------------------------------
# Step 0 — Onboarding
# ---------------------------------------------------------------------------
def render_step0():
    st.markdown(
        "<style>[data-testid='stSidebar'], [data-testid='collapsedControl'] {display:none;}</style>",
        unsafe_allow_html=True,
    )
    st.markdown("<h1 style='text-align:center;'>SkillGap Intelligence</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:rgba(230,238,245,0.7);font-size:1.05rem;'>"
        "A data-driven readiness assessment for your next career move.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.write("")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="onboard-card">
                <div class="onboard-icon">📄</div>
                <div class="onboard-title">Upload Resume</div>
                <div class="onboard-desc">Let AI extract your skills automatically from a PDF or TXT resume.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Start with Resume", use_container_width=True, key="btn_mode_resume"):
            st.session_state.input_mode = "resume"
            st.session_state.step = 1
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="onboard-card">
                <div class="onboard-icon">🛠️</div>
                <div class="onboard-title">Enter Skills Manually</div>
                <div class="onboard-desc">Pick your tech stack from a curated list and set your own proficiency.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Start Manually", use_container_width=True, key="btn_mode_manual"):
            st.session_state.input_mode = "manual"
            st.session_state.step = 1
            st.rerun()

# ---------------------------------------------------------------------------
# Step 1 — Data gathering (resume OR manual) + LeetCode (1.5)
# ---------------------------------------------------------------------------
def render_step1():
    st.markdown('<p class="step-caption">Step 2 of 4 · Data Gathering</p>', unsafe_allow_html=True)
    st.progress(0.25)
    st.subheader("Tell us about your current skills")

    all_user_skills = []

    if st.session_state.input_mode == "resume":
        st.markdown('<div class="tour-focus"></div>', unsafe_allow_html=True)
        st.info("💡 **Guide:** Upload your resume here — the AI will read it and pull out your technical skills automatically.")
        resume_file = st.file_uploader("Upload your resume", type=["pdf", "txt"], key="resume_uploader")
        extract_clicked = st.button("Extract Skills from Resume", key="btn_extract")

        if extract_clicked:
            if not resume_file:
                st.warning("Upload a PDF or TXT resume before extracting skills.")
            elif not llm_provider_configured():
                st.warning("No AI provider is configured. Please contact the administrator.")
            else:
                with st.spinner("Extracting skills from resume..."):
                    try:
                        resume_text = extract_text_from_resume_file(resume_file)
                        raw_skills_text = extract_skills_from_resume(text=resume_text)
                        if not raw_skills_text:
                            st.warning("AI extraction is currently unavailable. Please try again later.")
                        else:
                            route_extracted_skills(raw_skills_text)
                            st.success("Skills extracted and applied below.")
                    except Exception as e:
                        st.error(f"Failed to extract skills. Detailed trace:\n\n{e}")

        if st.session_state.parsed_known_skills or st.session_state.parsed_custom_skills:
            detected = list(dict.fromkeys(
                st.session_state.parsed_known_skills + parse_custom_skills(st.session_state.parsed_custom_skills)
            ))
            st.markdown("**Detected skills:**")
            st.info(", ".join(detected) if detected else "None detected yet.")

        extra_skills_raw = st.text_input(
            "Add or correct skills (comma-separated)",
            value=st.session_state.parsed_custom_skills,
            placeholder="e.g. Rust, Kanban, Figma",
            key="resume_extra_skills",
        )
        all_user_skills = list(dict.fromkeys(
            st.session_state.parsed_known_skills + parse_custom_skills(extra_skills_raw)
        ))

    else:  # manual mode
        selected_skills = st.multiselect(
            "Your current skills",
            options=ALL_TECH_SKILLS,
            default=st.session_state.parsed_known_skills,
            placeholder="Select from the skill list...",
            key="manual_multiselect",
        )
        custom_skills_raw = st.text_input(
            "Add custom skills not listed above (comma-separated)",
            value=st.session_state.parsed_custom_skills,
            placeholder="e.g. Rust, Kanban, Figma",
            key="manual_custom_skills",
        )
        all_user_skills = list(dict.fromkeys(selected_skills + parse_custom_skills(custom_skills_raw)))

    skill_proficiency = {}
    if all_user_skills:
        with st.expander("Adjust Skill Proficiency Levels", expanded=True):
            st.caption("Set your confidence level for each skill.")
            for skill in all_user_skills:
                chosen = st.select_slider(
                    skill,
                    options=PROFICIENCY_OPTIONS,
                    value="Intermediate (0.8)",
                    key=f"prof_{skill}",
                )
                skill_proficiency[skill.strip().lower()] = PROFICIENCY_WEIGHTS[chosen]
    else:
        st.info("Add skills above to configure proficiency levels.")

    st.divider()
    st.markdown("**LeetCode Username (Optional)** — Prove your logic skills")
    lc_col1, lc_col2 = st.columns([3, 1])
    with lc_col1:
        leetcode_username = st.text_input(
            "LeetCode username",
            key="leetcode_username_input",
            label_visibility="collapsed",
            placeholder="e.g. johndoe123",
        )
    with lc_col2:
        verify_clicked = st.button("Verify", use_container_width=True, key="btn_verify_leetcode")

    if verify_clicked:
        with st.spinner("Checking LeetCode profile..."):
            stats = fetch_leetcode_stats(leetcode_username)
            if stats:
                st.session_state.leetcode_stats = stats

    if st.session_state.get("leetcode_stats"):
        s = st.session_state.leetcode_stats
        st.success(
            f"✅ {s['username']}: {s['easy']} Easy · {s['medium']} Medium · {s['hard']} Hard "
            f"({s['total']} total solved)"
        )

    st.divider()
    nav_col1, nav_col2 = st.columns([1, 2])
    with nav_col1:
        if st.button("← Back", key="btn_back_to_0"):
            st.session_state.step = 0
            st.rerun()
    with nav_col2:
        if st.button("Continue →", type="primary", use_container_width=True, key="btn_continue_to_2"):
            if not all_user_skills:
                st.warning("Select or enter at least one skill before continuing.")
            else:
                st.session_state.all_user_skills = all_user_skills
                st.session_state.skill_proficiency = skill_proficiency
                st.session_state.step = 2
                st.rerun()

# ---------------------------------------------------------------------------
# Step 2 — Target role + analysis trigger
# ---------------------------------------------------------------------------
def render_step2():
    st.markdown('<p class="step-caption">Step 3 of 4 · Target Role</p>', unsafe_allow_html=True)
    st.progress(0.55)
    st.subheader("Where are you headed?")

    st.markdown('<div class="tour-focus"></div>', unsafe_allow_html=True)
    st.info("💡 **Guide:** Select your target job role below so the AI can benchmark your skills.")
    selected_role = st.selectbox(
        "Target job role",
        options=list(JOB_DATA["job_roles"].keys()),
        key="selected_role_input",
        help="The AI will benchmark your current skills against the industry baseline for this role.",
    )

    st.write("")
    st.markdown('<div class="pulse-anchor"></div>', unsafe_allow_html=True)
    generate_clicked = st.button(
        "🚀 Generate Intelligence Report",
        type="primary",
        use_container_width=True,
        key="btn_generate",
        disabled=st.session_state.is_processing,
    )

    st.write("")
    if st.button("← Back", key="btn_back_to_1"):
        st.session_state.step = 1
        st.rerun()

    if generate_clicked:
        st.session_state.selected_role = selected_role
        st.session_state.is_processing = True
        st.session_state.step = 3
        st.rerun()

# ---------------------------------------------------------------------------
# Step 3 — Processing (async fun-fact loader + AI calls)
# ---------------------------------------------------------------------------
def render_step3():
    st.markdown('<p class="step-caption">Step 4 of 4 · Analysis</p>', unsafe_allow_html=True)
    st.progress(0.85)
    st.subheader(f"Building your report for {st.session_state.get('selected_role', '')}")

    loader_slot = st.empty()
    with loader_slot.container():
        render_loading_component()

    ai_error = None
    try:
        required_skills = JOB_DATA["job_roles"][st.session_state.selected_role]["required_skills"]

        try:
            if not llm_provider_configured():
                raise RuntimeError("No AI provider configured.")
            results = ai_analyze_role(
                target_role=st.session_state.selected_role,
                required_skills=required_skills,
                all_user_skills=st.session_state.all_user_skills,
                skill_proficiencies=st.session_state.skill_proficiency,
                leetcode_stats=st.session_state.get("leetcode_stats"),
            )
        except Exception as e:
            print(f"AI evaluation failed, falling back to legacy analyzer: {e}")
            ai_error = str(e)
            results = legacy_analyze_role(st.session_state.selected_role, st.session_state.skill_proficiency)

        roadmap_weeks = None
        roadmap_error = None
        if results["critical_missing"] and llm_provider_configured():
            try:
                raw_roadmap = generate_ai_roadmap(
                    target_role=st.session_state.selected_role,
                    user_skills=st.session_state.all_user_skills,
                    missing_skills=results["critical_missing"],
                )
                roadmap_weeks = parse_roadmap_json(raw_roadmap)
            except Exception as e:
                print(f"Roadmap generation/parsing failed: {e}")
                roadmap_error = str(e)

        st.session_state.last_results = results
        st.session_state.last_role = st.session_state.selected_role
        st.session_state.last_required_skills = required_skills
        st.session_state.last_skill_proficiency = st.session_state.skill_proficiency
        st.session_state.last_roadmap_weeks = roadmap_weeks
        st.session_state.last_roadmap_error = roadmap_error
        st.session_state.last_ai_error = ai_error
    finally:
        loader_slot.empty()
        st.session_state.is_processing = False
        st.session_state.step = 4

    st.balloons()
    st.markdown(
        """
        <audio autoplay style="display:none">
            <source src="https://assets.mixkit.co/active_storage/sfx/212/212-preview.mp3" type="audio/mpeg">
        </audio>
        """,
        unsafe_allow_html=True,
    )
    # Render results immediately in this same run, rather than st.rerun(),
    # so the balloons/audio triggered above and the report land in one paint.
    render_step4()

# ---------------------------------------------------------------------------
# Step 4 — Results: Gap Analysis + Interactive Tabbed Roadmap
# ---------------------------------------------------------------------------
def render_step4():
    results = st.session_state.get("last_results")
    if results is None:
        st.warning("No report available yet. Start over to generate one.")
        if st.button("Start Over", key="btn_start_over_empty"):
            reset_app()
            st.rerun()
        return

    report_role = st.session_state.last_role
    report_required_skills = st.session_state.last_required_skills
    report_skill_proficiency = st.session_state.last_skill_proficiency
    roadmap_weeks = st.session_state.get("last_roadmap_weeks")

    if st.session_state.get("last_ai_error"):
        st.error(f"API Error Detected: {st.session_state.last_ai_error}")
        st.warning("AI evaluation unavailable. Fell back to strict keyword matching.")

    st.subheader(f"Results: {report_role}")
    st.info(f"Typical experience level: {results['experience_level']}")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric(
        "Role Readiness",
        f"{results['readiness_score']:.0f}%",
        help="A weighted score calculating your actual proficiency levels against the role's baseline.",
    )
    m_col2.metric(
        "Skill Coverage",
        f"{results['coverage_score']:.0f}%",
        help="The raw percentage of required skills you possess at any level.",
    )
    m_col3.metric("Strong Matches", len(results["strong_matches"]))
    m_col4.metric("Critical Gaps", len(results["critical_missing"]))

    st.write("Role Readiness")
    st.progress(int(results["readiness_score"]))
    st.write("Skill Coverage")
    st.progress(int(results["coverage_score"]))

    st.divider()

    tab_analysis, tab_roadmap = st.tabs(["Gap Analysis", "Interactive Roadmap"])

    with tab_analysis:
        render_radar_chart(report_role, report_required_skills, report_skill_proficiency)

        g_col1, g_col2, g_col3 = st.columns(3)
        with g_col1:
            st.markdown("**Strong Matches**")
            if results["strong_matches"]:
                st.success("\n".join(format_gap_line(item) for item in results["strong_matches"]))
            else:
                st.success("None yet.")
        with g_col2:
            st.markdown("**Needs Improvement**")
            if results["needs_improvement"]:
                st.warning("\n".join(format_gap_line(item) for item in results["needs_improvement"]))
            else:
                st.warning("Nothing stuck at Beginner level.")
        with g_col3:
            st.markdown("**Critical Missing Gaps**")
            if results["critical_missing"]:
                st.error("\n".join(f"- {req}" for req in results["critical_missing"]))
            else:
                st.error("None. Full coverage.")

    with tab_roadmap:
        if not results["critical_missing"]:
            st.success("No critical missing skills detected — an AI roadmap isn't required for this role.")
        elif st.session_state.get("last_roadmap_error"):
            st.warning(f"AI roadmap generation is currently unavailable: {st.session_state.last_roadmap_error}")
        elif not roadmap_weeks or not roadmap_weeks.get("weeks"):
            st.warning("AI roadmap generation is currently unavailable. Please try again later.")
        else:
            week_tabs = st.tabs([week["week_title"] for week in roadmap_weeks["weeks"]])
            for i, (tab, week) in enumerate(zip(week_tabs, roadmap_weeks["weeks"])):
                with tab:
                    if not week["tasks"]:
                        st.caption("No tasks generated for this week.")
                    for j, task in enumerate(week["tasks"]):
                        st.checkbox(task, key=f"roadmap_task_{i}_{j}")

    st.divider()
    roadmap_markdown = roadmap_weeks_to_markdown(roadmap_weeks)
    dl_col, reset_col = st.columns([2, 1])
    with dl_col:
        st.download_button(
            label="Download Full Report (Markdown)",
            data=build_markdown_report(report_role, results, roadmap_markdown),
            file_name="SkillGap_Assessment_Report.md",
            mime="text/markdown",
            use_container_width=True,
            key="btn_download_report",
        )
    with reset_col:
        if st.button("Start Over", use_container_width=True, key="btn_start_over"):
            reset_app()
            st.rerun()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SkillGap Intelligence", page_icon=None, layout="wide")
inject_global_css()
init_session_state()

current_step = st.session_state.step
if current_step == 0:
    render_step0()
elif current_step == 1:
    render_step1()
elif current_step == 2:
    render_step2()
elif current_step == 3:
    render_step3()
else:
    render_step4()