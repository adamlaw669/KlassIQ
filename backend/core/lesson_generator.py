"""
Environment variables expected:
 - LLM_API_URL  -> the HTTP endpoint for your LLM 
 - LLM_API_KEY  -> the API key for that endpoint
 - LLM_MODEL    -> optional model identifier 
"""

import os
import json
import time
import requests   # ensure `requests` is in your requirements
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

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
    except requests.exceptions.RequestException as e:
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
   "activities":[{"step":"Starter","time":"5 min","activity":"Show a mango, cut into halves. Discuss."}, ...],
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
    - curriculum_context: brief string summarizing the objectives from curriculum JSON (if empty, LLM will fallback)
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

    # 2) sanitize curriculum_context length - we must avoid huge prompts
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
