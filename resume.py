import io
import streamlit as st
import PyPDF2

from config import ALL_TECH_SKILLS
from llm import call_llm_resilient

def extract_skills_from_resume(text):
    prompt = f'Extract all technical skills, programming languages, and frameworks from the following resume text. Return ONLY a comma-separated list of skills. Do not include any other text, pleasantries, or markdown formatting. Text: {text}'
    return call_llm_resilient(prompt)
def extract_text_from_resume_file(uploaded_file):
    if uploaded_file.name.lower().endswith('.pdf'):
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        return '\n'.join((page.extract_text() or '' for page in reader.pages))
    else:
        return uploaded_file.getvalue().decode('utf-8', errors='ignore')
def route_extracted_skills(raw_skills_text):
    extracted = [s.strip() for s in raw_skills_text.split(',') if s.strip()]
    lookup = {skill.lower(): skill for skill in ALL_TECH_SKILLS}
    known_matches = []
    custom_matches = []
    for skill in extracted:
        canonical = lookup.get(skill.lower())
        if canonical:
            if canonical not in known_matches:
                known_matches.append(canonical)
        elif skill not in custom_matches:
            custom_matches.append(skill)
    st.session_state.parsed_known_skills = known_matches
    st.session_state.parsed_custom_skills = ', '.join(custom_matches)
