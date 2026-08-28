def format_gap_line(item):
    if isinstance(item, (tuple, list)) and len(item) == 2:
        req, weight = item
        return f'- {req} ({weight * 100:.0f}%)'
    return f'- {item}'
def format_priority_line(item, verb):
    if isinstance(item, (tuple, list)) and len(item) == 2:
        req, weight = item
        if verb == 'Strengthen':
            return f'{verb} {req} (currently {weight * 100:.0f}%)'
        return f'{verb} {req}'
    return f'{verb} {item}'
def build_markdown_report(role, results, roadmap_text):
    lines = [f'# SkillGap Assessment Report: {role}', '', f"**Experience Level:** {results['experience_level']}", '', f"**Role Readiness:** {results['readiness_score']:.0f}%", f"**Skill Coverage:** {results['coverage_score']:.0f}%", '', '## Strong Matches']
    if results['strong_matches']:
        lines.extend((format_gap_line(item) for item in results['strong_matches']))
    else:
        lines.append('- None yet.')
    lines.append('')
    lines.append('## Needs Improvement')
    if results['needs_improvement']:
        lines.extend((format_gap_line(item) for item in results['needs_improvement']))
    else:
        lines.append('- Nothing stuck at Beginner level.')
    lines.append('')
    lines.append('## Critical Gaps')
    if results['critical_missing']:
        lines.extend((f'- {req}' for req in results['critical_missing']))
    else:
        lines.append('- None. Full coverage.')
    lines.append('')
    lines.append('## 4-Week AI Roadmap')
    lines.append('')
    lines.append(roadmap_text if roadmap_text else '_No AI roadmap was generated for this assessment._')
    return '\n'.join(lines)
