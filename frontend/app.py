import streamlit as st
import requests
import json
# Removed unused import: traceback

from components.lesson_display import render_lesson_plan
from components.utils import LANGUAGES # Kept for list reference

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="KlassIQ - Lesson Design Assistant",
    layout="wide",
    page_icon="📘"
)

# Configuration
# NOTE: Using HTTPS for the live deployment URL
API_BASE_URL = "https://klassiq.onrender.com"

st.title("KlassIQ 📘")
st.markdown("**AI Lesson Design Assistant for Nigerian Educators**")
# NOTE: Ensure the path to your logo is correct
# st.image("./assets/KlassIQlogo.png", width=100) 

# --- UI Layout ---
# Use one main column for inputs, and the second column for output
col_input, col_output = st.columns([1.5, 3])

with col_input:
    st.markdown("---")
    st.subheader("Generate a Lesson Plan")
    
    # --- Input Form ---
    with st.form(key="lesson_form"):
        # Define columns for a cleaner layout of inputs
        col_sub, col_grade, col_topic = st.columns(3)
        with col_sub:
            subject = st.text_input("Subject", placeholder="e.g. Mathematics")
        with col_grade:
            grade = st.selectbox("Class/Grade", ["Primary 1", "Primary 2", "Primary 3",
                                                 "Primary 4", "Primary 5", "Primary 6",
                                                 "JSS 1", "JSS 2", "JSS 3"])
        with col_topic:
            topic = st.text_input("Topic", placeholder="e.g. Fractions")
        
        col_context, col_mode, col_empty = st.columns(3)
        with col_context:
            context = st.selectbox("Classroom Context", ["rural", "urban"])
        with col_mode:
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
    # 1. Input Validation
    if not subject or not topic:
        with col_output:
            st.error("🚨 Please enter a **Subject** and a **Topic** to generate a plan.")
        st.stop()

    # 2. API Call Execution
    with col_output:
        with st.spinner("Generating your lesson plan... ⏳ (This may take up to 90 seconds on first run)"):
            payload = {
                "subject": subject,
                "grade": grade,
                "topic": topic,
                "teacher_input": teacher_input,
                "language": "English", 
                "classroom_context": context,
                "output_mode": "short" if "Short" in mode else "full"
            }
            
            try:
                # Network Request
                resp = requests.post(f"{API_BASE_URL}/generate-plan", json=payload, timeout=90)
                resp.raise_for_status() # Raises HTTPError for 4xx/5xx status codes
                
                # JSON Parsing
                data = resp.json()
                result = data.get("result", {})
                
            except requests.exceptions.RequestException as e:
                # Catch connection, timeout, and HTTP status errors
                st.error(f"API CONNECTION ERROR. Server URL: `{API_BASE_URL}`")
                st.code(f"Details: {e}", language='text')
                st.stop()
            
            except json.JSONDecodeError:
                # Catch bad JSON response
                st.error("RESPONSE FORMAT ERROR. Server returned invalid data.")
                st.code(f"Raw Response: {resp.text[:500]}...", language='text')
                st.stop()
            
            # 3. Backend Logic Check (LLM/Parsing Failure)
            if "error" in result:
                st.error("GENERATION FAILED. The backend encountered an error.")
                st.code(result.get("error", "Unknown error"), language='text')
                
                if "raw" in result:
                     st.subheader("Raw LLM Output (for Debug):")
                     st.code(result["raw"], language='json')
                st.stop()
                
            # 4. Success and Rendering
            if result:
                st.success("✅ Lesson Plan Generated Successfully!")
                
                # Render the plan
                render_lesson_plan(result)

                # Downloadable JSON file
                st.download_button(
                    label="Download Lesson Plan JSON",
                    data=json.dumps(result, indent=2),
                    file_name=f"{topic.replace(' ', '_')}_lesson_plan.json",
                    mime="application/json"
                )