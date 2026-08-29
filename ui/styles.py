"""Global CSS + the fun-fact loading component. Unchanged visually from
Round 1 -- only relocated out of app.py."""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from data.catalog import FUN_FACTS


def inject_global_css() -> None:
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

        .main .block-container:has(.tour-focus) > div {
            opacity: 0.25;
            filter: blur(2px);
            pointer-events: none;
            transition: all 0.5s ease;
        }
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


def render_loading_component() -> None:
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
