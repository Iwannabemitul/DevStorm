"""
SkillGap Intelligence -- Round 2

Architecture:
    data/catalog.py            Static job-role + skill-catalog reference data.
    services/schema.py         Pydantic contracts for every LLM output / external payload.
    services/llm_engine.py     Singleton, resilient multi-provider LLM router + JSON repair.
    services/external_apis.py  LeetCode + GitHub verification (pure I/O, no Streamlit).
    services/resume_parser.py  Deterministic text extraction + skill-catalog mapping.
    services/analysis_service.py  Prompt construction + orchestration glue.
    ui/styles.py, ui/charts.py, ui/report.py   Presentation-only helpers.
    app.py (this file)         Session-state step machine + Streamlit caching only.

app.py deliberately contains no prompt strings, no JSON parsing, and no
`requests` calls -- if it needs to talk to an LLM or a third-party API, it
goes through a cached wrapper around a services/ function.
"""
import streamlit as st

from data.catalog import ALL_TECH_SKILLS, JOB_DATA, PROFICIENCY_OPTIONS, PROFICIENCY_WEIGHTS
from services.analysis_service import (
    ai_analyze_role,
    extract_skills_via_llm,
    generate_ai_roadmap,
    legacy_analyze_role,
)
from services.external_apis import build_candidate_verification, fetch_github_stats, fetch_leetcode_stats
from services.llm_engine import LLMEngine, LLMEngineError
from services.resume_parser import (
    extract_text_from_upload,
    map_tokens_to_skill_catalog,
    split_comma_list,
)
from services.schema import AnalysisResult, CandidateVerification, GitHubStats, LeetCodeStats, RoadmapResponse
from ui.charts import render_radar_chart
from ui.report import build_markdown_report, roadmap_to_markdown
from ui.styles import inject_global_css, render_loading_component


# --------------------------------------------------------------------------
# Cached wrappers around service calls
#
# Every intensive / network-bound / paid service call is wrapped here with
# @st.cache_data(ttl=3600, show_spinner=False). The LLMEngine instance is
# passed with a leading underscore so Streamlit excludes it from the cache
# key (it's a stateless router, not part of the "input"); everything else
# is a plain, hashable primitive so caching is fully deterministic.
# --------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def cached_extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    return extract_text_from_upload(filename, file_bytes)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_extract_skills_via_llm(_engine: LLMEngine, resume_text: str):
    return extract_skills_via_llm(_engine, resume_text)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_leetcode_stats(username: str):
    return fetch_leetcode_stats(username)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_github_stats(username: str):
    return fetch_github_stats(username)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_ai_analyze_role(
    _engine: LLMEngine,
    target_role: str,
    required_skills: tuple,
    all_user_skills: tuple,
    skill_proficiencies_items: tuple,
    verification_json: str,
) -> AnalysisResult:
    verification = CandidateVerification.model_validate_json(verification_json)
    return ai_analyze_role(
        _engine,
        target_role,
        list(required_skills),
        list(all_user_skills),
        dict(skill_proficiencies_items),
        verification,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def cached_generate_ai_roadmap(
    _engine: LLMEngine,
    target_role: str,
    user_skills: tuple,
    missing_skills: tuple,
) -> RoadmapResponse:
    return generate_ai_roadmap(_engine, target_role, list(user_skills), list(missing_skills))


def get_llm_engine() -> LLMEngine:
    engine = LLMEngine.get_instance()
    engine.configure(
        gemini_api_key=st.secrets.get("GEMINI_API_KEY"),
        nvidia_api_key=st.secrets.get("NVIDIA_API_KEY"),
    )
    return engine


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "step": 0,
        "input_mode": None,
        "parsed_known_skills": [],
        "parsed_custom_skills": "",
        "all_user_skills": [],
        "skill_proficiency": {},
        "leetcode_stats": None,
        "github_stats": None,
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


# --------------------------------------------------------------------------
# Step 0 -- entry mode
# --------------------------------------------------------------------------

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


# --------------------------------------------------------------------------
# Step 1 -- skills + verification
# --------------------------------------------------------------------------

def render_step1():
    engine = get_llm_engine()

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
            elif not engine.is_configured():
                st.warning("No AI provider is configured. Please contact the administrator.")
            else:
                with st.spinner("Extracting skills from resume..."):
                    try:
                        resume_text = cached_extract_text_from_upload(resume_file.name, resume_file.getvalue())
                        raw_tokens = cached_extract_skills_via_llm(engine, resume_text)
                        known, custom = map_tokens_to_skill_catalog(raw_tokens, ALL_TECH_SKILLS)
                        st.session_state.parsed_known_skills = known
                        st.session_state.parsed_custom_skills = ", ".join(custom)
                        st.success("Skills extracted and applied below.")
                    except LLMEngineError as e:
                        st.error(f"Failed to extract skills: {e}")

        if st.session_state.parsed_known_skills or st.session_state.parsed_custom_skills:
            detected = list(dict.fromkeys(
                st.session_state.parsed_known_skills + split_comma_list(st.session_state.parsed_custom_skills)
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
            st.session_state.parsed_known_skills + split_comma_list(extra_skills_raw)
        ))

    else:
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
        all_user_skills = list(dict.fromkeys(selected_skills + split_comma_list(custom_skills_raw)))

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
    st.markdown("**Verify with public coding profiles (optional)** — strengthens your report")

    lc_col1, lc_col2 = st.columns([3, 1])
    with lc_col1:
        leetcode_username = st.text_input(
            "LeetCode username",
            key="leetcode_username_input",
            placeholder="e.g. johndoe123",
        )
    with lc_col2:
        st.write("")
        verify_leetcode_clicked = st.button("Verify LeetCode", use_container_width=True, key="btn_verify_leetcode")

    if verify_leetcode_clicked:
        with st.spinner("Checking LeetCode profile..."):
            stats, note = cached_fetch_leetcode_stats(leetcode_username)
            if stats:
                st.session_state.leetcode_stats = stats
                st.toast(note, icon="⚠️" if stats.is_mock else "🏆")
            elif note:
                st.warning(note)

    if st.session_state.get("leetcode_stats"):
        s: LeetCodeStats = st.session_state.leetcode_stats
        mock_tag = " (demo data)" if s.is_mock else ""
        st.success(
            f"✅ {s.username}{mock_tag}: {s.easy} Easy · {s.medium} Medium · {s.hard} Hard "
            f"({s.total} total solved)"
        )

    gh_col1, gh_col2 = st.columns([3, 1])
    with gh_col1:
        github_username = st.text_input(
            "GitHub username",
            key="github_username_input",
            placeholder="e.g. johndoe",
        )
    with gh_col2:
        st.write("")
        verify_github_clicked = st.button("Verify GitHub", use_container_width=True, key="btn_verify_github")

    if verify_github_clicked:
        with st.spinner("Checking GitHub profile..."):
            gh_stats, gh_note = cached_fetch_github_stats(github_username)
            if gh_stats:
                st.session_state.github_stats = gh_stats
                st.toast(gh_note, icon="🐙")
            elif gh_note:
                st.warning(gh_note)

    if st.session_state.get("github_stats"):
        g: GitHubStats = st.session_state.github_stats
        langs = ", ".join(g.top_languages) if g.top_languages else "no detectable language"
        created = f" · since {g.account_created[:10]}" if g.account_created else ""
        st.success(f"✅ {g.username}: {g.public_repos} public repos · top languages: {langs}{created}")

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


# --------------------------------------------------------------------------
# Step 2 -- target role
# --------------------------------------------------------------------------

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


# --------------------------------------------------------------------------
# Step 3 -- analysis (transitional / processing step)
# --------------------------------------------------------------------------

def render_step3():
    engine = get_llm_engine()

    st.markdown('<p class="step-caption">Step 4 of 4 · Analysis</p>', unsafe_allow_html=True)
    st.progress(0.85)
    st.subheader(f"Building your report for {st.session_state.get('selected_role', '')}")

    loader_slot = st.empty()
    with loader_slot.container():
        render_loading_component()

    ai_error = None
    try:
        required_skills = JOB_DATA["job_roles"][st.session_state.selected_role]["required_skills"]
        experience_level = JOB_DATA["job_roles"][st.session_state.selected_role]["experience_level"]

        verification = build_candidate_verification(
            leetcode_stats=st.session_state.get("leetcode_stats"),
            github_stats=st.session_state.get("github_stats"),
        )

        try:
            if not engine.is_configured():
                raise LLMEngineError("No AI provider configured.")
            results = cached_ai_analyze_role(
                engine,
                st.session_state.selected_role,
                tuple(required_skills),
                tuple(st.session_state.all_user_skills),
                tuple(sorted(st.session_state.skill_proficiency.items())),
                verification.model_dump_json(),
            )
        except LLMEngineError as e:
            print(f"AI evaluation failed, falling back to legacy analyzer: {e}")
            ai_error = str(e)
            results = legacy_analyze_role(required_skills, st.session_state.skill_proficiency, experience_level)

        roadmap_weeks = None
        roadmap_error = None
        if results.critical_missing and engine.is_configured():
            try:
                roadmap_weeks = cached_generate_ai_roadmap(
                    engine,
                    st.session_state.selected_role,
                    tuple(st.session_state.all_user_skills),
                    tuple(results.critical_missing),
                )
            except LLMEngineError as e:
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
    render_step4()


# --------------------------------------------------------------------------
# Step 4 -- results
# --------------------------------------------------------------------------

def render_step4():
    results: AnalysisResult = st.session_state.get("last_results")
    if results is None:
        st.warning("No report available yet. Start over to generate one.")
        if st.button("Start Over", key="btn_start_over_empty"):
            reset_app()
            st.rerun()
        return

    report_role = st.session_state.last_role
    report_required_skills = st.session_state.last_required_skills
    report_skill_proficiency = st.session_state.last_skill_proficiency
    roadmap_weeks: RoadmapResponse = st.session_state.get("last_roadmap_weeks")

    if st.session_state.get("last_ai_error"):
        st.error(f"API Error Detected: {st.session_state.last_ai_error}")
        st.warning("AI evaluation unavailable. Fell back to strict keyword matching.")

    st.subheader(f"Results: {report_role}")
    st.info(f"Typical experience level: {results.experience_level}")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric(
        "Role Readiness",
        f"{results.readiness_score:.0f}%",
        help="A weighted score calculating your actual proficiency levels against the role's baseline.",
    )
    m_col2.metric(
        "Skill Coverage",
        f"{results.coverage_score:.0f}%",
        help="The raw percentage of required skills you possess at any level.",
    )
    m_col3.metric("Strong Matches", len(results.strong_matches))
    m_col4.metric("Critical Gaps", len(results.critical_missing))

    st.write("Role Readiness")
    st.progress(int(results.readiness_score))
    st.write("Skill Coverage")
    st.progress(int(results.coverage_score))

    st.divider()

    tab_analysis, tab_roadmap = st.tabs(["Gap Analysis", "Interactive Roadmap"])

    with tab_analysis:
        render_radar_chart(report_role, report_required_skills, report_skill_proficiency)

        g_col1, g_col2, g_col3 = st.columns(3)
        with g_col1:
            st.markdown("**Strong Matches**")
            if results.strong_matches:
                st.success("\n".join(f"- {item}" for item in results.strong_matches))
            else:
                st.success("None yet.")
        with g_col2:
            st.markdown("**Needs Improvement**")
            if results.needs_improvement:
                st.warning("\n".join(f"- {item}" for item in results.needs_improvement))
            else:
                st.warning("Nothing stuck at Beginner level.")
        with g_col3:
            st.markdown("**Critical Missing Gaps**")
            if results.critical_missing:
                st.error("\n".join(f"- {req}" for req in results.critical_missing))
            else:
                st.error("None. Full coverage.")

    with tab_roadmap:
        if not results.critical_missing:
            st.success("No critical missing skills detected — an AI roadmap isn't required for this role.")
        elif st.session_state.get("last_roadmap_error"):
            st.warning(f"AI roadmap generation is currently unavailable: {st.session_state.last_roadmap_error}")
        elif not roadmap_weeks or not roadmap_weeks.weeks:
            st.warning("AI roadmap generation is currently unavailable. Please try again later.")
        else:
            week_tabs = st.tabs([week.week_title for week in roadmap_weeks.weeks])
            for i, (tab, week) in enumerate(zip(week_tabs, roadmap_weeks.weeks)):
                with tab:
                    if not week.tasks:
                        st.caption("No tasks generated for this week.")
                    for j, task in enumerate(week.tasks):
                        st.checkbox(task, key=f"roadmap_task_{i}_{j}")

    st.divider()
    roadmap_markdown = roadmap_to_markdown(roadmap_weeks)
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


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

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
