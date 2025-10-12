import streamlit as st

def render_lesson_plan(data: dict):
    """Render the generated lesson plan neatly in Streamlit UI."""
    st.markdown("### Lesson Plan Overview")
    st.markdown(f"#### {data.get('title', 'Untitled')}")
    st.markdown("---")

    sections = [
        (" Objectives", data.get("objectives")),
        (" Learning Outcomes", data.get("learning_outcomes")),
        (" Introduction", data.get("introduction")),
        (" Activities", data.get("activities")),
        (" Differentiation", data.get("differentiation")),
        (" Materials", data.get("materials")),
        (" Assessment", data.get("assessment")),
        (" Classroom Management", data.get("classroom_management")),
        (" Extension", data.get("extension")),
        (" Low-Data Version", data.get("low_data_version")),
        (" Notes", data.get("notes")),
    ]

    for title, content in sections:
        with st.expander(title, expanded=True):
            if isinstance(content, list):
                for item in content:
                    st.markdown(f"- {item}")
            elif isinstance(content, str):
                st.markdown(content)
            elif isinstance(content, dict):
                for k, v in content.items():
                    st.markdown(f"**{k}:** {v}")
            else:
                st.markdown("_No content available._")
