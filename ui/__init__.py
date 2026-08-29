"""Presentation-layer helpers (CSS, charts, report formatting) kept separate
from services/ so the Streamlit-specific code doesn't bleed into the
service-oriented backend. Only app.py orchestrates step state; these modules
are pure render/format helpers."""
