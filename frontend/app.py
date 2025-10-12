import streamlit as st
import requests
import json
from components.lesson_display import render_lesson_plan
from components.utils import translate_text, LANGUAGES

st.set_page_config(
    page_title="KlassIQ - Lesson Design Assistant",
    layout="wide",
    page_icon="📘"
)

API_BASE_URL = "klassiq.onrender.com"  # replace with FastAPI URL (when hosted)
DEFAULT_LANG = "English"


st.title("KlassIQ📘")
st.markdown("**AI Lesson Design Assistant for Nigerian Educators**")
st.image("frontend/assets/KlassIQlogo.png", width=100)


col1, col2 = st.columns([1.5, 3])
with col1:
    st.subheader("Language")
    language = st.selectbox(
        "Choose your preferred language:",
        LANGUAGES,
        index=0
    )

st.session_state["language"] = language

st.markdown("---")
st.subheader("Generate a Lesson Plan")

with st.form(key="lesson_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        subject = st.text_input("Subject", placeholder="e.g. Mathematics")
        grade = st.selectbox("Class/Grade", ["Primary 1", "Primary 2", "Primary 3",
                                             "Primary 4", "Primary 5", "Primary 6",
                                             "JSS 1", "JSS 2", "JSS 3"])
    with col2:
        topic = st.text_input("Topic", placeholder="e.g. Fractions")
        context = st.selectbox("Classroom Context", ["rural", "urban"])
    with col3:
        mode = st.radio("Lesson Length", ["Full Plan", "Short Summary"], horizontal=True)

    teacher_input = st.text_area(
        "Optional: Describe materials or constraints (optional)",
        placeholder="I have mangoes and cardboard for teaching fractions..."
    )

    submit = st.form_submit_button("✨ Generate Lesson Plan")

# -------------------------------
# GENERATE PLAN LOGIC
# -------------------------------
if submit:
    with st.spinner("Generating your lesson plan... ⏳"):
        payload = {
            "subject": subject,
            "grade": grade,
            "topic": topic,
            "teacher_input": teacher_input,
            "language": language,
            "classroom_context": context,
            "output_mode": "short" if "Short" in mode else "full"
        }

        try:
            resp = requests.post(f"{API_BASE_URL}/generate-plan", json=payload)
            resp.raise_for_status()
            data = resp.json()
            result = data.get("result", {})
        except Exception as e:
            st.error(f"Request failed: {e}")
            result = {}

        if result:
            # Optional: translate lesson to selected language
            if language != DEFAULT_LANG:
                with st.spinner(f"Translating content to {language}..."):
                    result = translate_text(result, language)

            st.success("Lesson Plan Generated!")
            render_lesson_plan(result)

            # Downloadable JSON file
            st.download_button(
                label="Download Lesson Plan JSON",
                data=json.dumps(result, indent=2),
                file_name=f"{topic.replace(' ', '_')}_lesson_plan.json",
                mime="application/json"
            )
