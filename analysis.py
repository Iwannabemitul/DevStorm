import json

from config import JOB_DATA
from llm import call_llm_resilient

def legacy_analyze_role(selected_role, skill_proficiency):
    role_info = JOB_DATA['job_roles'][selected_role]
    required_skills = role_info['required_skills']
    total_required = len(required_skills)
    strong_matches = []
    needs_improvement = []
    critical_missing = []
    earned_weight_sum = 0.0
    covered_count = 0
    for requirement in required_skills:
        options = [opt.strip().lower() for opt in requirement.split('/')]
        matched_weights = [skill_proficiency[opt] for opt in options if opt in skill_proficiency]
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
    coverage_score = covered_count / total_required * 100 if total_required else 0
    readiness_score = earned_weight_sum / total_required * 100 if total_required else 0
    return {'experience_level': role_info['experience_level'], 'total_required': total_required, 'coverage_score': coverage_score, 'readiness_score': readiness_score, 'strong_matches': strong_matches, 'needs_improvement': needs_improvement, 'critical_missing': critical_missing}
def ai_analyze_role(target_role, required_skills, all_user_skills, skill_proficiencies):
    proficiency_lines = ', '.join((f'{skill} ({weight * 100:.0f}% proficiency)' for skill, weight in skill_proficiencies.items())) or 'none provided'
    prompt = f"""Act as a Senior Technical Recruiter. Semantically evaluate a candidate's skills against the required skills for the target role of {target_role}. Required skills for this role: {required_skills}. Candidate's stated skills: {all_user_skills}. Candidate's proficiency levels: {proficiency_lines}. Do not rely on exact string matching. If the candidate has an advanced or adjacent skill that demonstrates competence in a required skill (for example, knowing PyTorch implies competence in Feature Engineering or Machine Learning), credit them for it and note the inference in parentheses. Return ONLY a raw JSON string matching this exact schema, with no markdown formatting, no backticks, and no extra text before or after it: {{"readiness_score": 85, "coverage_score": 90, "experience_level_assessment": "Mid to Senior", "strong_matches": ["Python (Advanced)", "Machine Learning (via PyTorch)"], "needs_improvement": ["Docker (Beginner)"], "critical_missing": ["Cloud Architecture"]}}"""
    raw_text = call_llm_resilient(prompt)
    if not raw_text:
        raise RuntimeError('No AI provider returned a response.')
    if raw_text.startswith('```'):
        raw_text = raw_text.strip('`')
        if raw_text.lower().startswith('json'):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()
    parsed = json.loads(raw_text)
    return {'experience_level': parsed['experience_level_assessment'], 'total_required': len(required_skills), 'coverage_score': parsed['coverage_score'], 'readiness_score': parsed['readiness_score'], 'strong_matches': parsed['strong_matches'], 'needs_improvement': parsed['needs_improvement'], 'critical_missing': parsed['critical_missing']}
def generate_ai_roadmap(target_role, user_skills, missing_skills):
    prompt = f'Act as a Senior Tech Recruiter and Mentor. The user wants to be a {target_role}. They currently know {user_skills} with varying proficiencies. They are completely missing these critical skills: {missing_skills}. Write a highly specific, no-nonsense 4-week learning roadmap to close this gap. Do not use generic filler. Recommend specific types of projects they should build. For every major section, weekly header, and key tool mentioned in the roadmap: 1. Turn the title or tool into a clickable Markdown link pointing to a YouTube search query. 2. Format the URL as: https://www.youtube.com/results?search_query=TOPIC+NAME+tutorial (replace spaces with + or URL encoding). 3. Example format: ### [Week 3: MLOps & Experiment Tracking](https://www.youtube.com/results?search_query=MLOps+Experiment+Tracking+Crash+Course) - [MLflow & DVC Pipeline Setup](https://www.youtube.com/results?search_query=MLflow+DVC+pipeline+tutorial): Setup experiment tracking... Do not hallucinate raw watch links (e.g. watch?v=...). Always use formatted [youtube.com/results?search_query=](https://youtube.com/results?search_query=) links.'
    return call_llm_resilient(prompt)
