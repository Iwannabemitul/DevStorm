import streamlit as st

from config import ALL_TECH_SKILLS, JOB_DATA, PROFICIENCY_OPTIONS, PROFICIENCY_WEIGHTS
from analysis import ai_analyze_role, generate_ai_roadmap, legacy_analyze_role
from charts import render_radar_chart
from llm import llm_provider_configured
from reports import build_markdown_report, format_gap_line, format_priority_line
from resume import extract_skills_from_resume, extract_text_from_resume_file, route_extracted_skills
from utils import parse_custom_skills

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
                raw_skills_text = extract_skills_from_resume(resume_text)
                if not raw_skills_text:
                    st.warning("AI extraction is currently unavailable. Please try again later.")
                else:
                    route_extracted_skills(raw_skills_text)
                    st.success("Skills extracted and applied below.")
            except Exception as e:
                st.error(f"Failed to extract skills. Detailed trace:\n\n{e}")

st.divider()

col1, col2 = st.columns(2)

with col1:
    selected_role = st.selectbox(
        "Target job role",
        options=list(JOB_DATA["job_roles"].keys()),
    )

with col2:
    selected_skills = st.multiselect(
        "Your current skills",
        options=ALL_TECH_SKILLS,
        default=st.session_state.parsed_known_skills,
        placeholder="Select from the skill list...",
    )

custom_skills_raw = st.text_input(
    "Add custom skills not listed above (comma-separated)",
    value=st.session_state.parsed_custom_skills,
    placeholder="e.g. Rust, Kanban, Figma",
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
                key=f"prof_{skill}",
            )
            skill_proficiency[skill.strip().lower()] = PROFICIENCY_WEIGHTS[chosen]
else:
    st.info("Select skills above, or add custom ones, to configure proficiency levels.")

st.divider()

analyze_clicked = st.button(
    "Analyze",
    type="primary",
    disabled=st.session_state.is_processing,
)

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
