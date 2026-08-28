import streamlit as st

JOB_DATA = {
    "job_roles": {
        "Software Engineer": {
            "required_skills": ["Data Structures & Algorithms", "Python/Java/C++", "Git & Version Control", "System Design", "Debugging & Testing"],
            "experience_level": "Entry to Senior"
        },
        "Data Scientist": {
            "required_skills": ["Python/R", "Statistics & Probability", "Machine Learning", "SQL", "Data Visualization"],
            "experience_level": "Mid to Senior"
        },
        "Product Manager": {
            "required_skills": ["Roadmap Planning", "Stakeholder Communication", "Market Research", "Agile/Scrum", "Data-Driven Decision Making"],
            "experience_level": "Mid to Senior"
        },
        "UX/UI Designer": {
            "required_skills": ["Wireframing & Prototyping", "Figma/Sketch/Adobe XD", "User Research", "Interaction Design", "Visual Design Principles"],
            "experience_level": "Entry to Senior"
        },
        "DevOps Engineer": {
            "required_skills": ["CI/CD Pipelines", "Docker & Kubernetes", "Cloud Platforms (AWS/Azure/GCP)", "Infrastructure as Code (Terraform)", "Linux Administration"],
            "experience_level": "Mid to Senior"
        },
        "Database Administrator": {
            "required_skills": ["SQL & NoSQL Databases", "Query Optimization", "Backup & Recovery", "Database Security", "Performance Tuning"],
            "experience_level": "Mid to Senior"
        },
        "Cybersecurity Analyst": {
            "required_skills": ["Network Security", "Threat Detection & Response", "Penetration Testing", "SIEM Tools", "Risk Assessment"],
            "experience_level": "Entry to Senior"
        },
        "Digital Marketing Specialist": {
            "required_skills": ["SEO/SEM", "Content Strategy", "Social Media Marketing", "Google Analytics", "Email Marketing Campaigns"],
            "experience_level": "Entry to Mid"
        }
    }
}

PROFICIENCY_OPTIONS = ["Beginner (0.4)", "Intermediate (0.8)", "Advanced (1.0)"]
PROFICIENCY_WEIGHTS = {
    "Beginner (0.4)": 0.4,
    "Intermediate (0.8)": 0.8,
    "Advanced (1.0)": 1.0,
}


def build_unique_skill_list(job_data):
    """Flatten JOB_DATA into a sorted list of unique atomic skills,
    splitting slash-grouped requirements into individual entries."""
    unique_skills = set()
    for role_info in job_data["job_roles"].values():
        for requirement in role_info["required_skills"]:
            for option in requirement.split("/"):
                unique_skills.add(option.strip())
    return sorted(unique_skills)


def parse_custom_skills(raw_text):
    return [s.strip() for s in raw_text.split(",") if s.strip()]


def analyze_role(selected_role, skill_proficiency):
    """skill_proficiency: dict of {skill_name_lower: weight_float}"""
    role_info = JOB_DATA["job_roles"][selected_role]
    required_skills = role_info["required_skills"]
    total_required = len(required_skills)

    strong_matches = []      # (requirement, weight)
    needs_improvement = []   # (requirement, weight)
    critical_missing = []    # requirement

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


st.set_page_config(page_title="Skill-Gap Analyzer", page_icon="🎯", layout="wide")

st.title("🎯 Skill-Gap Analyzer")
st.caption("Find out how your current skills stack up against a target job role — with proficiency-weighted scoring.")

st.divider()

unique_skills = build_unique_skill_list(JOB_DATA)

col1, col2 = st.columns(2)

with col1:
    selected_role = st.selectbox(
        "Select a job role",
        options=list(JOB_DATA["job_roles"].keys())
    )

with col2:
    selected_skills = st.multiselect(
        "Select your current skills",
        options=unique_skills,
        placeholder="Choose from known skills..."
    )

custom_skills_raw = st.text_input(
    "Add custom skills not listed above (comma-separated)",
    placeholder="e.g. Rust, Kanban, Figma"
)
custom_skills = parse_custom_skills(custom_skills_raw)

all_user_skills = list(dict.fromkeys(selected_skills + custom_skills))  # de-duped, order preserved

skill_proficiency = {}

if all_user_skills:
    with st.expander("Adjust Skill Proficiency Levels", expanded=True):
        st.caption("Set how confident you are in each skill you've added.")
        for skill in all_user_skills:
            chosen = st.select_slider(
                skill,
                options=PROFICIENCY_OPTIONS,
                value="Intermediate (0.8)",
                key=f"prof_{skill}"
            )
            skill_proficiency[skill.strip().lower()] = PROFICIENCY_WEIGHTS[chosen]
else:
    st.info("Select skills above (or add custom ones) to set proficiency levels.")

st.divider()

analyze_clicked = st.button("Analyze", type="primary")

if analyze_clicked:
    if not all_user_skills:
        st.warning("Please select or enter at least one skill before analyzing.")
    else:
        results = analyze_role(selected_role, skill_proficiency)

        st.subheader(f"Results for: {selected_role}")
        st.info(f"**Typical experience level:** {results['experience_level']}")

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Role Readiness (Weighted)", f"{results['readiness_score']:.0f}%")
        m_col2.metric("Skill Coverage", f"{results['coverage_score']:.0f}%")
        m_col3.metric("Strong Matches", len(results["strong_matches"]))
        m_col4.metric("Critical Gaps", len(results["critical_missing"]))

        st.write("**Role Readiness**")
        st.progress(int(results["readiness_score"]))
        st.write("**Skill Coverage**")
        st.progress(int(results["coverage_score"]))

        st.divider()

        tab_analysis, tab_action_plan = st.tabs(["📊 Gap Analysis", "🗺️ Action Plan"])

        with tab_analysis:
            g_col1, g_col2, g_col3 = st.columns(3)

            with g_col1:
                st.markdown("### 🟢 Strong Matches")
                if results["strong_matches"]:
                    lines = [f"- {req} ({w * 100:.0f}%)" for req, w in results["strong_matches"]]
                    st.success("\n".join(lines))
                else:
                    st.success("None yet.")

            with g_col2:
                st.markdown("### 🟡 Needs Improvement")
                if results["needs_improvement"]:
                    lines = [f"- {req} ({w * 100:.0f}%)" for req, w in results["needs_improvement"]]
                    st.warning("\n".join(lines))
                else:
                    st.warning("None — nothing stuck at Beginner.")

            with g_col3:
                st.markdown("### 🔴 Critical Missing Gaps")
                if results["critical_missing"]:
                    lines = [f"- {req}" for req in results["critical_missing"]]
                    st.error("\n".join(lines))
                else:
                    st.error("None — full coverage!")

        with tab_action_plan:
            st.markdown("### Priority Breakdown")
            st.caption("Tackle these in order for the fastest path to role readiness.")

            priority_num = 1

            if results["critical_missing"]:
                st.markdown("**Priority 1 — Close critical gaps (skills you don't have at all):**")
                for req in results["critical_missing"]:
                    st.markdown(f"{priority_num}. Learn **{req}**")
                    priority_num += 1
                st.write("")

            if results["needs_improvement"]:
                st.markdown("**Priority 2 — Level up Beginner skills:**")
                for req, w in results["needs_improvement"]:
                    st.markdown(f"{priority_num}. Strengthen **{req}** (currently {w * 100:.0f}%) toward Intermediate/Advanced")
                    priority_num += 1
                st.write("")

            if not results["critical_missing"] and not results["needs_improvement"]:
                st.success("You're fully covered and proficient across all required skills for this role!")
            else:
                st.info(
                    f"Completing all {priority_num - 1} items above would bring your "
                    f"Role Readiness Score to 100%."
                )