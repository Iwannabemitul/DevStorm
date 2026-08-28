def parse_custom_skills(raw_text):
    return [s.strip() for s in raw_text.split(',') if s.strip()]
