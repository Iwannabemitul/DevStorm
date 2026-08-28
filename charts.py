import streamlit as st
import plotly.graph_objects as go

def render_radar_chart(selected_role, required_skills, skill_proficiency):
    categories = []
    user_values = []
    for requirement in required_skills:
        label = requirement.split('/')[0].strip()
        categories.append(label)
        options = [opt.strip().lower() for opt in requirement.split('/')]
        matched_weights = [skill_proficiency[opt] for opt in options if opt in skill_proficiency]
        user_values.append(max(matched_weights) if matched_weights else 0.0)
    if not categories:
        return
    categories_closed = categories + [categories[0]]
    user_values_closed = user_values + [user_values[0]]
    baseline_values_closed = [1.0] * len(categories_closed)

    def proficiency_label(value):
        labels = {0.0: 'None (0%)', 0.4: 'Beginner (40%)', 0.8: 'Intermediate (80%)', 1.0: 'Advanced (100%)'}
        return labels.get(value, f'{value * 100:.0f}%')
    current_levels_closed = [proficiency_label(value) for value in user_values_closed]
    hover_data = list(zip(categories_closed, current_levels_closed))
    chart_config = {'displayModeBar': False, 'staticPlot': False, 'scrollZoom': False}
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=baseline_values_closed, theta=categories_closed, name='Role Baseline', mode='lines+markers', line=dict(color='rgba(156, 163, 175, 0.5)', dash='dash'), marker=dict(size=7, color='rgba(156, 163, 175, 0.9)'), fill='toself', fillcolor='rgba(156, 163, 175, 0.05)', customdata=hover_data, hovertemplate='<b>%{customdata[0]}</b><br>Your current level: %{customdata[1]}<br>Required: 100%<extra>Role baseline</extra>'))
    fig.add_trace(go.Scatterpolar(r=user_values_closed, theta=categories_closed, name='Your Profile', mode='lines+markers', line=dict(color='#2DD4BF', width=3), marker=dict(size=9, color='#2DD4BF', line=dict(color='#FFFFFF', width=1)), fill='toself', fillcolor='rgba(45, 212, 191, 0.4)', customdata=hover_data, hovertemplate='<b>%{customdata[0]}</b><br>Your current level: %{customdata[1]}<br>Required: 100%<extra>Your profile</extra>'))
    if sum((value > 0 for value in user_values)) <= 1:
        fig.add_trace(go.Scatterpolar(r=[0], theta=[categories[0]], mode='markers', marker=dict(size=8, color='rgba(45, 212, 191, 0.65)'), hoverinfo='skip', showlegend=False))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1.0], tickvals=[0, 0.4, 0.8, 1.0], ticktext=['0%', '40% (Beginner)', '80% (Intermediate)', '100% (Advanced)'], ticks='', gridcolor='rgba(255, 255, 255, 0.28)', gridwidth=1, linecolor='rgba(0,0,0,0)', color='#CBD5E1', tickfont=dict(size=11)), angularaxis=dict(gridcolor='rgba(255, 255, 255, 0.18)', linecolor='rgba(0,0,0,0)', tickfont=dict(color='#E2E8F0', size=13)), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'), showlegend=True, legend=dict(orientation='h', yanchor='bottom', y=1.15, xanchor='center', x=0.5), title=dict(text=f'Skill Profile vs. {selected_role} Baseline', x=0.5, font=dict(size=16)), margin=dict(t=80, b=20), dragmode=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config)
    with st.expander('Skill Fulfillment Bar Chart', expanded=True):
        st.caption('Each bar shows how closely your current level meets the 100% requirement.')
        fulfillment_percentages = [value * 100 for value in user_values]
        bar_colors = ['#22C55E' if value >= 80 else '#EAB308' if value >= 40 else '#EF4444' for value in fulfillment_percentages]
        bar_fig = go.Figure(go.Bar(x=fulfillment_percentages, y=categories, orientation='h', marker_color=bar_colors, text=[f'{value:.0f}%' for value in fulfillment_percentages], textposition='auto', customdata=hover_data[:-1], hovertemplate='<b>%{customdata[0]}</b><br>Your current level: %{customdata[1]}<br>Required: 100%<extra></extra>'))
        bar_fig.update_layout(xaxis=dict(title='Fulfillment of role requirement', range=[0, 100], ticksuffix='%', tickvals=[0, 40, 80, 100], gridcolor='rgba(255, 255, 255, 0.15)'), yaxis=dict(autorange='reversed'), height=max(260, len(categories) * 48), margin=dict(l=20, r=30, t=20, b=45), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'), showlegend=False, dragmode=False)
        st.plotly_chart(bar_fig, use_container_width=True, config=chart_config)
