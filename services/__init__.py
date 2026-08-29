"""Service-oriented backend layer for the SkillGap Intelligence app.

Each module here owns one concern:
  - schema.py         Pydantic contracts for every LLM output and external payload.
  - llm_engine.py      The resilient, singleton multi-provider LLM router.
  - external_apis.py   LeetCode + GitHub verification (network I/O, no Streamlit).
  - resume_parser.py   Deterministic resume text extraction + skill mapping.
  - analysis_service.py  Business logic that glues the above together into the
                          scores and roadmaps the UI renders.

Nothing in `services/` imports `streamlit`. That keeps the layer independently
testable and makes the caching boundary (`st.cache_data`) live entirely in app.py.
"""
