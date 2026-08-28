import streamlit as st
import google.generativeai as genai
import PyPDF2
import io
import json
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

def parse_custom_skills(raw_text):
    return [s.strip() for s in raw_text.split(",") if s.strip()]

def get_gemini_api_keys():
    """Return configured Gemini keys in failover order, without exposing them."""
    configured_keys = st.secrets.get("GEMINI_API_KEYS", [])
    if isinstance(configured_keys, str):
        # Also accept a comma-separated value for hosts whose secret UI has no list editor.
        configured_keys = configured_keys.split(",")
    elif not isinstance(configured_keys, (list, tuple)):
        configured_keys = [configured_keys]

    keys = [str(key).strip() for key in configured_keys if key and str(key).strip()]

    # Keep the original single-key secret working during and after migration.
    legacy_key = st.secrets.get("GEMINI_API_KEY")
    if legacy_key and str(legacy_key).strip():
        keys.append(str(legacy_key).strip())

    # Preserve priority order while preventing the same key from being tried twice.
    return list(dict.fromkeys(keys))

def llm_provider_configured():
    return bool(get_gemini_api_keys()) or bool(st.secrets.get("NVIDIA_API_KEY"))

def call_llm_resilient(prompt):
    errors = []

    # Each key is attempted in order. A quota/rate-limit error on one key simply
    # moves to the next key; if all fail, the caller uses the non-AI fallback.
    for key_number, gemini_key in enumerate(get_gemini_api_keys(), start=1):
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
            # Do not include secret values or provider details in the user-facing error.
            errors.append(f"Gemini key {key_number} was unavailable")
            print(f"Gemini key {key_number} failed: {e}")

    nvidia_key = st.secrets.get("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=nvidia_key)
            completion = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct",  # <--- CHANGE TO 3.3 OR 3.2
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

def ai_analyze_role(target_role, required_skills, all_user_skills, skill_proficiencies):
    proficiency_lines = ", ".join(
        f"{skill} ({weight * 100:.0f}% proficiency)" for skill, weight in skill_proficiencies.items()
    ) or "none provided"

    prompt = (
        "Act as a Senior Technical Recruiter. Semantically evaluate a candidate's skills against "
        f"the required skills for the target role of {target_role}. "
        f"Required skills for this role: {required_skills}. "
        f"Candidate's stated skills: {all_user_skills}. "
        f"Candidate's proficiency levels: {proficiency_lines}. "
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
        f"Write a highly specific, no-nonsense 4-week learning roadmap to close this gap. "
        f"Do not use generic filler. Recommend specific types of projects they should build. "
        "For every major section, weekly header, and key tool mentioned in the roadmap: "
        "1. Turn the title or tool into a clickable Markdown link pointing to a YouTube search query. "
        "2. Format the URL as: https://www.youtube.com/results?search_query=TOPIC+NAME+tutorial "
        "(replace spaces with + or URL encoding). "
        "3. Example format: "
        "### [Week 3: MLOps & Experiment Tracking](https://www.youtube.com/results?search_query=MLOps+Experiment+Tracking+Crash+Course) "
        "- [MLflow & DVC Pipeline Setup](https://www.youtube.com/results?search_query=MLflow+DVC+pipeline+tutorial): Setup experiment tracking... "
        "Do not hallucinate raw watch links (e.g. watch?v=...). Always use formatted "
        "[youtube.com/results?search_query=](https://youtube.com/results?search_query=) links."
    )
    return call_llm_resilient(prompt)

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


st.set_page_config(page_title="SkillGap Intelligence", page_icon=None, layout="wide")

if "parsed_known_skills" not in st.session_state:
    st.session_state.parsed_known_skills = []
if "parsed_custom_skills" not in st.session_state:
    st.session_state.parsed_custom_skills = ""
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "last_role" not in st.session_state:
    st.session_state.last_role = None
if "last_required_skills" not in st.session_state:
    st.session_state.last_required_skills = []
if "last_skill_proficiency" not in st.session_state:
    st.session_state.last_skill_proficiency = {}
if "last_roadmap" not in st.session_state:
    st.session_state.last_roadmap = ""

st.title("SkillGap Intelligence")
st.caption("A data-driven readiness assessment for your next career move.")

st.divider()

resume_file = st.file_uploader("Upload your resume", type=["pdf", "txt"])
extract_clicked = st.button("Extract Skills from Resume")

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
                # The explicit API error will display here
                st.error(f"Failed to extract skills. Detailed trace:\n\n{e}")

st.divider()

col1, col2 = st.columns(2)

with col1:
    selected_role = st.selectbox(
        "Target job role",
        options=list(JOB_DATA["job_roles"].keys())
    )

with col2:
    selected_skills = st.multiselect(
        "Your current skills",
        options=ALL_TECH_SKILLS,
        default=st.session_state.parsed_known_skills,
        placeholder="Select from the skill list..."
    )

custom_skills_raw = st.text_input(
    "Add custom skills not listed above (comma-separated)",
    value=st.session_state.parsed_custom_skills,
    placeholder="e.g. Rust, Kanban, Figma"
)
custom_skills = parse_custom_skills(custom_skills_raw)

all_user_skills = list(dict.fromkeys(selected_skills + custom_skills))

skill_proficiency = {}

if all_user_skills:
    with st.expander("Adjust Skill Proficiency Levels", expanded=True):
        st.caption("Set your confidence level for each skill.")
        for skill in all_user_skills:
            chosen = st.select_slider(
                skill,
                options=PROFICIENCY_OPTIONS,
                value="Intermediate (0.8)",
                key=f"prof_{skill}"
            )
            skill_proficiency[skill.strip().lower()] = PROFICIENCY_WEIGHTS[chosen]
else:
    st.info("Select skills above, or add custom ones, to configure proficiency levels.")

st.divider()

analyze_clicked = st.button("Analyze", type="primary", disabled=st.session_state.is_processing)

def format_gap_line(item):
    if isinstance(item, (tuple, list)) and len(item) == 2:
        req, weight = item
        return f"- {req} ({weight * 100:.0f}%)"
    return f"- {item}"

def format_priority_line(item, verb):
    if isinstance(item, (tuple, list)) and len(item) == 2:
        req, weight = item
        if verb == "Strengthen":
            return f"{verb} {req} (currently {weight * 100:.0f}%)"
        return f"{verb} {req}"
    return f"{verb} {item}"

if analyze_clicked:
    if not all_user_skills:
        st.warning("Select or enter at least one skill before analyzing.")
    else:
        st.session_state.is_processing = True
        try:
            required_skills = JOB_DATA["job_roles"][selected_role]["required_skills"]

            with st.status("Evaluating Skill Profile...", expanded=True) as status:
                status.write("Analyzing extracted technical stack...")

                try:
                    if not llm_provider_configured():
                        raise RuntimeError("No AI provider configured.")

                    status.write("Evaluating semantic alignment with target role...")
                    results = ai_analyze_role(
                        target_role=selected_role,
                        required_skills=required_skills,
                        all_user_skills=all_user_skills,
                        skill_proficiencies=skill_proficiency,
                    )
                except Exception as e:
                    print(f"AI evaluation failed, falling back to legacy analyzer: {e}")
                    # Surface explicit AI error to user instead of silent fallback
                    st.error(f"API Error Detected: {e}")
                    st.warning("AI evaluation unavailable. Falling back to strict keyword matching.")
                    results = legacy_analyze_role(selected_role, skill_proficiency)

                status.write("Structuring gap analysis and readiness metrics...")

                roadmap_text = ""
                if results["critical_missing"] and llm_provider_configured():
                    try:
                        roadmap_text = generate_ai_roadmap(
                            target_role=selected_role,
                            user_skills=all_user_skills,
                            missing_skills=results["critical_missing"],
                        )
                    except Exception as e:
                        print(f"Roadmap generation failed: {e}")
                        roadmap_text = ""

                status.update(label="Analysis Complete", state="complete", expanded=False)

            st.session_state.last_results = results
            st.session_state.last_role = selected_role
            st.session_state.last_required_skills = required_skills
            st.session_state.last_skill_proficiency = skill_proficiency
            st.session_state.last_roadmap = roadmap_text
        finally:
            st.session_state.is_processing = False

if st.session_state.last_results is not None:
    results = st.session_state.last_results
    report_role = st.session_state.last_role
    report_required_skills = st.session_state.last_required_skills
    report_skill_proficiency = st.session_state.last_skill_proficiency
    roadmap_text = st.session_state.last_roadmap

    st.subheader(f"Results: {report_role}")
    st.info(f"Typical experience level: {results['experience_level']}")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Role Readiness", f"{results['readiness_score']:.0f}%")
    m_col2.metric("Skill Coverage", f"{results['coverage_score']:.0f}%")
    m_col3.metric("Strong Matches", len(results["strong_matches"]))
    m_col4.metric("Critical Gaps", len(results["critical_missing"]))

    st.write("Role Readiness")
    st.progress(int(results["readiness_score"]))
    st.write("Skill Coverage")
    st.progress(int(results["coverage_score"]))

    st.divider()

    tab_analysis, tab_action_plan = st.tabs(["Gap Analysis", "Action Plan"])

    with tab_analysis:
        render_radar_chart(report_role, report_required_skills, report_skill_proficiency)

        g_col1, g_col2, g_col3 = st.columns(3)

        with g_col1:
            st.markdown("**Strong Matches**")
            if results["strong_matches"]:
                lines = [format_gap_line(item) for item in results["strong_matches"]]
                st.success("\n".join(lines))
            else:
                st.success("None yet.")

        with g_col2:
            st.markdown("**Needs Improvement**")
            if results["needs_improvement"]:
                lines = [format_gap_line(item) for item in results["needs_improvement"]]
                st.warning("\n".join(lines))
            else:
                st.warning("Nothing stuck at Beginner level.")

        with g_col3:
            st.markdown("**Critical Missing Gaps**")
            if results["critical_missing"]:
                lines = [f"- {req}" for req in results["critical_missing"]]
                st.error("\n".join(lines))
            else:
                st.error("None. Full coverage.")

    with tab_action_plan:
        st.markdown("### Priority Breakdown")
        st.caption("Recommended order of attack for the fastest path to role readiness.")

        priority_num = 1

        if results["critical_missing"]:
            st.markdown("**Priority 1: Close critical gaps (skills you don't have at all)**")
            for req in results["critical_missing"]:
                st.markdown(f"{priority_num}. {format_priority_line(req, 'Learn')}")
                priority_num += 1

        if results["needs_improvement"]:
            st.markdown("**Priority 2: Level up Beginner skills**")
            for item in results["needs_improvement"]:
                st.markdown(f"{priority_num}. {format_priority_line(item, 'Strengthen')}")
                priority_num += 1

        if not results["critical_missing"] and not results["needs_improvement"]:
            st.success("Full coverage and proficiency across all required skills for this role.")

        st.divider()
        st.markdown("### AI-Generated Learning Roadmap")

        if not results["critical_missing"]:
            st.info("No critical missing skills detected. An AI roadmap is not required for this role.")
        elif not llm_provider_configured():
            st.warning("No AI provider configured. Please contact the administrator.")
        elif not roadmap_text:
            st.warning("AI roadmap generation is currently unavailable. Please try again later.")
        else:
            st.markdown(roadmap_text)

        st.divider()
        st.download_button(
            label="Download Full Report (Markdown)",
            data=build_markdown_report(report_role, results, roadmap_text),
            file_name="SkillGap_Assessment_Report.md",
            mime="text/markdown",
        )
