import streamlit as st

def render_lesson_plan(data: dict):
    """Renders the structured lesson plan data neatly in the Streamlit UI."""
    
    # 1. Initial Data Check
    if not data or data.get('error'):
        st.warning("⚠️ Cannot display the lesson plan: data is missing or contains an error.")
        return
        
    st.markdown("### Lesson Plan Overview")
    st.markdown(f"#### {data.get('title', 'Untitled Lesson Plan')}")
    st.markdown("---")

    # 2. Define Section Order and Content Retrieval
    sections = [
        ("Objectives", data.get("objectives")),
        ("Learning Outcomes", data.get("learning_outcomes")),
        ("Introduction", data.get("introduction")),
        ("Activities", data.get("activities")),
        ("Differentiation", data.get("differentiation")),
        ("Materials", data.get("materials")),
        ("Assessment", data.get("assessment")),
        ("Classroom Management", data.get("classroom_management")),
        ("Extension", data.get("extension")),
        ("Low-Data Version", data.get("low_data_version")),
        ("Notes", data.get("notes")),
    ]

    # 3. Render Sections
    for title, content in sections:
        # Check if the content is a list of complex objects (Activities or Low-Data)
        is_nested_list = title in ("Activities", "Low-Data Version")
        
        # Keep 'Objectives' expanded by default
        expanded_state = (title == "Objectives")
        
        with st.expander(f"📚 {title}", expanded=expanded_state):
            
            if isinstance(content, list):
                
                # Handle LISTS OF DICTIONARIES (e.g., Main Activities)
                if is_nested_list and content and isinstance(content[0], dict):
                    for i, item in enumerate(content):
                        name = item.get('name', f'Activity {i+1}')
                        st.markdown(f"**{i+1}. {name}**")
                        
                        details = []
                        if 'description' in item:
                            details.append(f"Description: {item['description']}")
                        if 'duration' in item:
                            details.append(f"Duration: {item['duration']}")
                            
                        if details:
                            # &emsp; provides horizontal spacing
                            st.markdown(f"&emsp;* {'; '.join(details)}")
                        st.markdown("---")
                        
                # Handle LISTS OF STRINGS (e.g., Objectives, Learning Outcomes)
                else:
                    for item in content:
                        st.markdown(f"- {str(item)}")
                        
            elif isinstance(content, dict):
                
                # Handle the specific nested DICT structure of 'Low-Data Version'
                if title == "Low-Data Version" and "activities" in content:
                    st.markdown("##### Minimal Plan Details:")
                    for key, value in content.items():
                        if key == 'objectives' and isinstance(value, list):
                            st.markdown("**Objectives:**")
                            for obj in value:
                                st.markdown(f"- {obj}")
                        elif key == 'activities' and isinstance(value, list):
                            st.markdown("**Activities:**")
                            # Render nested activities list
                            for i, activity in enumerate(value):
                                st.markdown(f"**{i+1}. {activity.get('name', 'Activity')}**")
                                if 'description' in activity:
                                     st.markdown(f"&emsp;* Description: {activity['description']}")
                                
                # Handle Generic DICTIONARY (e.g., Differentiation)
                else:
                    for k, v in content.items():
                        # Standard title case formatting for keys
                        st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
                        
            elif isinstance(content, str):
                # Handle single STRING content (e.g., Introduction, Notes)
                st.markdown(content)

            else:
                st.markdown("_No content provided for this section._")