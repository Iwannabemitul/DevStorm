import streamlit as st
import google.generativeai as genai
from openai import OpenAI

def llm_provider_configured():
    return bool(st.secrets.get('GEMINI_API_KEY')) or bool(st.secrets.get('NVIDIA_API_KEY'))
def call_llm_resilient(prompt):
    errors = []
    gemini_key = st.secrets.get('GEMINI_API_KEY')
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            candidate_priority = ['models/gemini-3.6-flash', 'models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-2.0-flash', 'models/gemini-pro']
            selected_model_name = None
            for candidate in candidate_priority:
                if candidate in available_models:
                    selected_model_name = candidate
                    break
            if selected_model_name is None and available_models:
                selected_model_name = available_models[0]
            if selected_model_name is None:
                raise RuntimeError('No Gemini models supporting generateContent are available.')
            model = genai.GenerativeModel(selected_model_name)
            response = model.generate_content(prompt)
            text = (response.text or '').strip()
            if text:
                return text
            raise RuntimeError('Gemini returned an empty response.')
        except Exception as e:
            errors.append(f'Gemini Error: {str(e)}')
            print(f'Gemini call failed: {e}')
    nvidia_key = st.secrets.get('NVIDIA_API_KEY')
    if nvidia_key:
        try:
            client = OpenAI(base_url='https://integrate.api.nvidia.com/v1', api_key=nvidia_key)
            completion = client.chat.completions.create(model='meta/llama-3.3-70b-instruct-v2', messages=[{'role': 'user', 'content': prompt}], max_tokens=1500, temperature=0.2)
            text = (completion.choices[0].message.content or '').strip()
            if text:
                return text
            raise RuntimeError('NVIDIA returned an empty response.')
        except Exception as e:
            errors.append(f'NVIDIA Error: {str(e)}')
            print(f'NVIDIA fallback call failed: {e}')
    if errors:
        raise RuntimeError(' | '.join(errors))
    return ''
