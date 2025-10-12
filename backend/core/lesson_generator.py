"""
Environment variables expected:
 - LLM_API_URL  -> the HTTP endpoint for your LLM 
 - LLM_API_KEY  -> the API key for that endpoint
 - LLM_MODEL    -> optional model identifier 
"""

import os
import json
import time
try:
    import requests
except ImportError:
    # Fallback if requests is not available
    requests = None
    print("Warning: requests module not available. HTTP calls will be disabled.")
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Union

# Simple file-based cache for generated plans (avoid repeat API calls during demo)
CACHE_DIR = Path(__file__).resolve().parents[1] / "tmp_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LLM_API_URL = os.environ.get("LLM_API_URL", "").strip()
LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()
LLM_MODEL = os.environ.get("LLM_MODEL", "").strip()  # optional, used if API requires a model name

# Basic safety: ensure API credentials are set (but don't die loudly in prod)
if not LLM_API_URL or not LLM_API_KEY:
    # we allow offline runs (local placeholder) but warn
    print("Warning: LLM_API_URL or LLM_API_KEY not configured. The lesson generator will use a local fallback.")


def normalize_grade(grade: str) -> str:
    """
    Normalize grade input to match curriculum structure.
    
    Args:
        grade: Input grade (e.g., "JSS 1", "Primary 4", "Junior Secondary 1")
        
    Returns:
        str: Normalized grade matching curriculum structure
    """
    grade_lower = grade.lower().strip()
    
    # JSS mappings
    if any(term in grade_lower for term in ['jss', 'junior secondary', 'js']):
        return "Junior Secondary 1–3"
    
    # Primary mappings
    if 'primary' in grade_lower or 'pri' in grade_lower:
        # Extract number if present
        for char in grade_lower:
            if char.isdigit():
                num = int(char)
                if num in [1, 2, 3]:
                    return "Primary 1–3"
                elif num in [4, 5, 6]:
                    return "Primary 4–6"
                break
        # Default to Primary 1-3 if no number found
        return "Primary 1–3"
    
    # Direct matches
    grade_mappings = {
        "junior secondary 1–3": "Junior Secondary 1–3",
        "primary 1–3": "Primary 1–3", 
        "primary 4–6": "Primary 4–6"
    }
    
    return grade_mappings.get(grade_lower, grade)


def normalize_subject(subject: str) -> str:
    """
    Normalize subject input to match curriculum structure.
    
    Args:
        subject: Input subject name
        
    Returns:
        str: Normalized subject name
    """
    subject_lower = subject.lower().strip()
    
    # Subject mappings
    subject_mappings = {
        'english': 'english_studies',
        'mathematics': 'maths',
        'math': 'maths',
        'science': 'basic_science_technology',
        'basic science': 'basic_science_technology',
        'technology': 'basic_science_technology',
        'creative arts': 'cca',
        'arts': 'cca',
        'cca': 'cca',
        'christian religious studies': 'crs',
        'crs': 'crs',
        'islamic studies': 'islamic',
        'islamic': 'islamic',
        'hausa': 'hausa',
        'igbo': 'igbo',
        'yoruba': 'yoruba',
        'french': 'french',
        'arabic': 'arabic',
        'history': 'history',
        'nvc': 'nvc',
        'prevoc': 'prevoc'
    }
    
    return subject_mappings.get(subject_lower, subject)


def get_curriculum_objectives(grade: str, subject: str, topic: str) -> Dict[str, Union[List[str], str]]:
    """
    Fetch curriculum objectives for a specific grade, subject, and topic.
    
    Args:
        grade: Grade level (e.g., "Primary 1–3", "Primary 4–6", "Junior Secondary 1–3")
        subject: Subject name (e.g., "english_studies", "maths", "basic_science_technology")
        topic: Topic name to search for
        
    Returns:
        Dict containing objectives, content, activities, and resources or error message
    """
    try:
        # Normalize inputs
        grade = normalize_grade(grade)
        subject = normalize_subject(subject)
        
        # Load the merged curriculum map
        curriculum_path = Path(__file__).resolve().parents[1] / "data" / "curriculum_map.json"
        
        if not curriculum_path.exists():
            return {
                "error": "Curriculum map not found. Please run merge_curriculums.py first.",
                "objectives": [],
                "content": [],
                "teacher_activities": [],
                "student_activities": [],
                "resources": []
            }
            
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            curriculum_data = json.load(f)
            
        # Check if grade level exists
        if grade not in curriculum_data:
            available_grades = list(curriculum_data.keys())
            return {
                "error": f"Grade '{grade}' not found. Available grades: {available_grades}",
                "objectives": [],
                "content": [],
                "teacher_activities": [],
                "student_activities": [],
                "resources": []
            }
            
        grade_data = curriculum_data[grade]
        
        # Check if subject exists in this grade
        if subject not in grade_data:
            available_subjects = list(grade_data.keys())
            return {
                "error": f"Subject '{subject}' not found in {grade}. Available subjects: {available_subjects}",
                "objectives": [],
                "content": [],
                "teacher_activities": [],
                "student_activities": [],
                "resources": []
            }
            
        subject_data = grade_data[subject]
        
        # Search recursively for the topic in all levels, themes, sub-themes
        def search_topic_recursive(data: Dict, search_topic: str) -> Optional[Dict]:
            """Recursively search for a topic in the curriculum structure."""
            search_topic_lower = search_topic.lower().strip()
            
            if isinstance(data, dict):
                # Check if we're at a level with THEMES (like PRIMARY 1, JSS1, etc.)
                if "THEMES" in data:
                    themes = data["THEMES"]
                    if isinstance(themes, list):
                        for theme in themes:
                            if isinstance(theme, dict) and "SUB THEMES" in theme:
                                sub_themes = theme["SUB THEMES"]
                                if isinstance(sub_themes, list):
                                    for sub_theme in sub_themes:
                                        if isinstance(sub_theme, dict) and "TOPICS" in sub_theme:
                                            topics = sub_theme["TOPICS"]
                                            if isinstance(topics, list):
                                                for topic_item in topics:
                                                    if isinstance(topic_item, dict) and "TOPIC NAME" in topic_item:
                                                        topic_name = topic_item["TOPIC NAME"].lower().strip()
                                                        if search_topic_lower in topic_name or topic_name in search_topic_lower:
                                                            return topic_item
                
                # Recursively search in nested structures
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        result = search_topic_recursive(value, search_topic)
                        if result:
                            return result
                            
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, (dict, list)):
                        result = search_topic_recursive(item, search_topic)
                        if result:
                            return result
                            
            return None
        
        # Search for the topic
        topic_data = search_topic_recursive(subject_data, topic)
        
        if not topic_data:
            return {
                "error": f"Topic '{topic}' not found in {subject} for {grade}",
                "objectives": [],
                "content": [],
                "teacher_activities": [],
                "student_activities": [],
                "resources": []
            }
        
        # Extract the curriculum information
        result = {
            "objectives": topic_data.get("PERFORMANCE OBJECTIVES", []),
            "content": topic_data.get("CONTENT", []),
            "teacher_activities": topic_data.get("TEACHER ACTIVITIES", []),
            "student_activities": topic_data.get("STUDENTS ACTIVITIES", topic_data.get("PUPILS ACTIVITIES", [])),
            "resources": topic_data.get("TEACHING AND LEARNING RESOURCES", [])
        }
        
        # Add topic name for context
        if "TOPIC NAME" in topic_data:
            result["topic_name"] = topic_data["TOPIC NAME"]
            
        return result
        
    except Exception as e:
        return {
            "error": f"Error retrieving curriculum objectives: {str(e)}",
            "objectives": [],
            "content": [],
            "teacher_activities": [],
            "student_activities": [],
            "resources": []
        }


def _cache_key(subject: str, grade: str, topic: str, teacher_input: Optional[str], language: str, summary_mode: bool):
    raw = json.dumps([subject, grade, topic, teacher_input or "", language, summary_mode], sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _write_cache(key: str, value: Dict):
    p = CACHE_DIR / f"{key}.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def _read_cache(key: str) -> Optional[Dict]:
    p = CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _call_llm(prompt: str, max_tokens: int = 1200, temperature: float = 0.2) -> str:
    """
    Generic LLM HTTP caller. Expects a JSON response with 'text' or similar.
    Configure LLM_API_URL and LLM_API_KEY in env.
    This function is intentionally generic so you can point it at your provider.
    """
    if not LLM_API_URL or not LLM_API_KEY:
        # Offline fallback: return a templated stub plan (useful for local dev)
        return json.dumps({
            "title": "SAMPLE LESSON - offline mode",
            "objectives": ["(offline) practice objective 1", "(offline) practice objective 2"],
            "introduction": "Introduce topic briefly (offline fallback).",
            "activities": ["Activity 1 (discussion)", "Activity 2 (hands-on)"],
            "assessment": ["Ask students to summarize key points"],
            "materials": ["Local objects, chalk, paper"],
            "notes": "Offline fallback used because no LLM credentials configured."
        })
    
    if requests is None:
        # No requests module available - return offline fallback
        return json.dumps({
            "title": "SAMPLE LESSON - requests module not available",
            "objectives": ["(no-requests) practice objective 1", "(no-requests) practice objective 2"],
            "introduction": "Introduce topic briefly (no HTTP capability).",
            "activities": ["Activity 1 (discussion)", "Activity 2 (hands-on)"],
            "assessment": ["Ask students to summarize key points"],
            "materials": ["Local objects, chalk, paper"],
            "notes": "HTTP requests not available - using fallback response."
        })

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": LLM_MODEL or "default",
        "messages": [
            {"role": "system", "content": "You are a clear, practical education expert who writes lesson plans for low-resource classrooms in Nigeria."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # try common paths for the generated text
        # Many providers use data["choices"][0]["message"]["content"]
        if isinstance(data, dict):
            # path 1: OpenAI-style
            try:
                return data["choices"][0]["message"]["content"]
            except Exception:
                pass
            # path 2: simple text
            if "text" in data:
                return data["text"]
            # path 3: top-level output
            # If provider returns JSON string directly
            return json.dumps(data)
        return str(data)
    except Exception as e:
        # rate-limit or network error: return a helpful message for the frontend
        return json.dumps({"error": f"LLM request failed: {str(e)}"})



PROMPT_TEMPLATE = """
You are an expert curriculum designer and veteran primary/secondary teacher who writes short, practical, context-aware lesson plans for low-resource classrooms in Nigeria.
Your job: produce a single, tightly-structured lesson plan JSON for the teacher's input below. Be concise and practical.

CONTEXT (Curriculum objectives found for the requested topic):
{curriculum_context}

TEACHER INPUT:
- Grade: {grade}
- Subject: {subject}
- Topic: {topic}
- Language: {language}
- Classroom context: {classroom_context}
- Available materials/tools (teacher provided): {teacher_input}
- Output mode: {output_mode}

REQUIREMENTS:
1) Return **only valid JSON** (no extra explanation or markdown). The top-level object must include exactly these keys:
   - title (string)
   - objectives (list of short strings, 2-4 items)
   - learning_outcomes (list of short measurable outcomes 2-4 items)
   - introduction (1-2 short paragraphs; how to hook students)
   - activities (list of step-by-step activities; include approximate time for each)
   - differentiation (short suggestions for low/high ability or large class)
   - materials (list of items teachers can use; prefer local, low-cost materials)
   - assessment (list of 2-4 quick assessment items or formative tasks)
   - classroom_management (2-3 short practical tips)
   - extension (optional homework / community link)
   - low_data_version (string) - a 1-paragraph, printer-friendly version (short)
   - notes (short safety / sensitivity / cultural considerations)
2) Make sure all examples and contextualized references are realistic for Nigerian primary/JSS classrooms.
3) Keep language simple. Avoid advanced jargon. Use local examples when possible (market, farm, household, local transport, common materials).
4) If curriculum_context is empty or lacks specifics, generate a safe generic plan aligned to the subject and grade.
5) If teacher_input describes specific materials, adapt at least one activity to use those materials.
6) If {output_mode} == "short", produce minimal, compact outputs (shorter activities, 1-2 objectives).
7) Do NOT include policy prescriptions or clinical advice (no health diagnoses).
8) Keep answer length restricted to what fits typical LLM token limits; be concise.

Here are two JSON examples to show style and format (ONLY for style - do not copy exact language):

EXAMPLE 1:
{{ "title":"Local Fractions (Primary 4)",
   "objectives":["Understand halves and quarters", "Use everyday objects to demonstrate fractions"],
   "learning_outcomes":["Divide an object into 2 equal parts","Identify halves in pictures"],
   "introduction":"Ask pupils if they have shared food... (short)",
   "activities":["Starter (5 min): Show a mango, cut into halves. Discuss.", "Main activity: Practice dividing objects", "Conclusion: Review key concepts"],
   "differentiation":["Pair weaker learners with stronger peers","Use larger concrete objects for low-vision pupils"],
   "materials":["mango or orange, paper, chalk"],
   "assessment":["Group show-and-tell","Short board exercise: draw half of the shape"],
   "classroom_management":["Assign roles to groups","Use simple hand signals"],
   "extension":"Ask pupils to find halves at home",
   "low_data_version":"Starter: show a fruit. Activity: ask pupils to divide a drawing into halves.",
   "notes":"Be sensitive when using examples involving food distribution; ensure fairness."
}}

EXAMPLE 2:
{{ "title":"Intro to Soil and Plants (Primary 5)",
   "objectives":[...], "learning_outcomes":[...], ... }}

END PROMPT.
"""


def generate_lesson_plan(
    subject: str,
    grade: str,
    topic: str,
    curriculum_context: Optional[str] = None,
    teacher_input: Optional[str] = None,
    language: str = "English",
    classroom_context: str = "rural",
    output_mode: str = "full",    # "full" or "short"
    use_cache: bool = True
) -> Dict:
    """
    Main entry point for the backend.
    - subject, grade, topic: provided by the frontend
    - curriculum_context: brief string summarizing the objectives from curriculum JSON (if None, will auto-retrieve)
    - teacher_input: optional free text describing materials or constraints
    - language: lesson output language (basic support - instruct LLM)
    - classroom_context: 'rural' or 'urban' (affects examples)
    - output_mode: 'full' or 'short' (for low-data / quick plans)
    """

    # 1) try cache
    key = _cache_key(subject, grade, topic, teacher_input, language, output_mode == "short")
    if use_cache:
        cached = _read_cache(key)
        if cached:
            return {"from_cache": True, "result": cached}

    # 2) Get curriculum context - either provided or auto-retrieve
    if curriculum_context is None:
        # Auto-retrieve curriculum objectives
        curriculum_objectives = get_curriculum_objectives(grade, subject, topic)
        
        if "error" not in curriculum_objectives:
            # Format the curriculum context
            context_parts = []
            
            if curriculum_objectives.get("topic_name"):
                context_parts.append(f"Topic: {curriculum_objectives['topic_name']}")
                
            if curriculum_objectives.get("objectives"):
                context_parts.append(f"Performance Objectives: {'; '.join(curriculum_objectives['objectives'])}")
                
            if curriculum_objectives.get("content"):
                content_str = '; '.join(curriculum_objectives['content'])
                if len(content_str) > 500:  # Truncate if too long
                    content_str = content_str[:497] + "..."
                context_parts.append(f"Content: {content_str}")
                
            if curriculum_objectives.get("teacher_activities"):
                activities_str = '; '.join(curriculum_objectives['teacher_activities'])
                if len(activities_str) > 300:  # Truncate if too long
                    activities_str = activities_str[:297] + "..."
                context_parts.append(f"Teacher Activities: {activities_str}")
                
            curriculum_context = " | ".join(context_parts)
        else:
            curriculum_context = f"(auto-retrieval failed: {curriculum_objectives.get('error', 'unknown error')})"
    
    # Sanitize curriculum_context length - we must avoid huge prompts
    if curriculum_context:
        # keep to reasonable length, trim if needed
        curriculum_context = curriculum_context.strip()
        if len(curriculum_context) > 4000:
            curriculum_context = curriculum_context[:3900] + " ... [truncated]"
    else:
        curriculum_context = "(no curriculum context provided)"

    # 3) build prompt
    prompt = PROMPT_TEMPLATE.format(
        curriculum_context=curriculum_context,
        grade=grade,
        subject=subject,
        topic=topic,
        language=language,
        classroom_context=classroom_context,
        teacher_input=teacher_input or "None provided",
        output_mode=("short" if output_mode == "short" else "full"),
    )

    # 4) call the LLM
    llm_response_text = _call_llm(prompt, max_tokens=1200, temperature=0.15)

    # 5) attempt to parse as JSON
    parsed = None
    try:
        parsed = json.loads(llm_response_text)
    except Exception:
        # some LLMs may return JSON inside text; try to extract the first JSON object
        import re
        match = re.search(r"(\{[\s\S]*\})", llm_response_text)
        if match:
            try:
                parsed = json.loads(match.group(1))
            except Exception:
                parsed = {"error": "Failed to parse JSON from LLM output", "raw": llm_response_text}
        else:
            parsed = {"error": "LLM did not return JSON", "raw": llm_response_text}

    # 6) store cache and return
    if isinstance(parsed, dict):
        _write_cache(key, parsed)

    return {"from_cache": False, "result": parsed}
