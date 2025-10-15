"""
LLM Service Module for Generating Lesson Plans

This module provides functions to fetch curriculum data, normalize inputs, 
and generate structured lesson plans by directly calling the Google Gemini API.

Environment variables expected:
 - GEMINI_API_KEY -> The API key for the Gemini service.
 - LLM_MODEL      -> Optional model identifier (default: 'gemini-2.0-flash').
 
NOTE: All debugging prints, caching, and fallback logic have been removed.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
from google import genai
from google.genai import types
import re # Keep regex for robust JSON parsing

# --- Configuration & Initialization ---

# Environment variables - hardcoded for deployment stability
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or "AIzaSyAhkD0dv_JIv9ZVCqzLOPNUhkr6hjEf1eI"
LLM_MODEL = os.getenv("LLM_MODEL", 'gemini-2.0-flash').strip()

# Initialize Gemini Client (will be set when API key is available)
CLIENT = None

def _ensure_client():
    """Initialize the Gemini client if not already done."""
    global CLIENT
    print(f"🔑 _ensure_client called, CLIENT is: {CLIENT}")
    if CLIENT is None:
        print(f"🔐 API key check: {GEMINI_API_KEY[:10]}..." if GEMINI_API_KEY else "❌ No API key")
        if not GEMINI_API_KEY:
            print(f"❌ GEMINI_API_KEY is missing!")
            raise ValueError(
                "GEMINI_API_KEY environment variable is required for API client initialization. "
                "Please set this environment variable in your deployment settings (Render.com dashboard > Environment tab) "
                "with a valid Google Gemini API key from https://aistudio.google.com/app/apikey"
            )
        print(f"🚀 Initializing Gemini client...")
        CLIENT = genai.Client(api_key=GEMINI_API_KEY)
        print('✅ Gemini api loaded successfully')
    else:
        print(f"♻️ Using existing Gemini client")
    return CLIENT


# --- Utility Functions: Normalization ---

def normalize_grade(grade: str) -> str:
    """Normalize grade input to match curriculum structure."""
    grade_lower = grade.lower().strip()
    
    # JSS mappings
    if any(term in grade_lower for term in ['jss', 'junior secondary', 'js']):
        return "Junior Secondary 1–3"
    
    # Primary mappings
    if 'primary' in grade_lower or 'pri' in grade_lower:
        for char in grade_lower:
            if char.isdigit():
                num = int(char)
                if num in [1, 2, 3]:
                    return "Primary 1–3"
                elif num in [4, 5, 6]:
                    return "Primary 4–6"
                break
        return "Primary 1–3"
    
    # Direct matches
    grade_mappings = {
        "junior secondary 1–3": "Junior Secondary 1–3",
        "primary 1–3": "Primary 1–3", 
        "primary 4–6": "Primary 4–6"
    }
    
    return grade_mappings.get(grade_lower, grade)


def normalize_subject(subject: str) -> str:
    """Normalize subject input to match curriculum structure."""
    subject_lower = subject.lower().strip()
    
    subject_mappings = {
        'english': 'english_studies',
        'mathematics': 'maths',
        'math': 'maths',
        'science': 'basic_science_technology',
        'basic science': 'basic_science_technology',
        'technology': 'basic_science_technology',
        'creative arts': 'cca',
        'arts': 'cca',
        'crs': 'crs',
        'christian religious studies': 'crs',
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


# --- Curriculum Retrieval ---

def get_curriculum_objectives(grade: str, subject: str, topic: str) -> Dict[str, Union[List[str], str]]:
    """Fetch curriculum objectives for a specific grade, subject, and topic from the local map."""
    try:
        grade = normalize_grade(grade)
        subject = normalize_subject(subject)
        
        curriculum_path = Path(__file__).resolve().parents[1] / "data" / "curriculum_map.json"
        
        if not curriculum_path.exists():
            return {"error": "Curriculum map file not found."}
            
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            curriculum_data = json.load(f)
            
        if grade not in curriculum_data:
            return {"error": f"Grade '{grade}' not found. Available: {list(curriculum_data.keys())}"}
            
        grade_data = curriculum_data[grade]
        
        if subject not in grade_data:
            return {"error": f"Subject '{subject}' not found in {grade}. Available: {list(grade_data.keys())}"}
            
        subject_data = grade_data[subject]
        
        # Recursive search function (kept simplified)
        def search_topic_recursive(data: Union[Dict, List], search_topic: str) -> Optional[Dict]:
            search_topic_lower = search_topic.lower().strip()
            
            if isinstance(data, dict):
                if "TOPIC NAME" in data:
                    topic_name = data["TOPIC NAME"].lower().strip()
                    if search_topic_lower in topic_name or topic_name in search_topic_lower:
                        return data

                for value in data.values():
                    result = search_topic_recursive(value, search_topic)
                    if result:
                        return result
                            
            elif isinstance(data, list):
                for item in data:
                    result = search_topic_recursive(item, search_topic)
                    if result:
                        return result
                            
            return None
        
        topic_data = search_topic_recursive(subject_data, topic)
        
        if not topic_data:
            return {"error": f"Topic '{topic}' not found in {subject} for {grade}"}
        
        # Extract and map the curriculum information
        result = {
            "objectives": topic_data.get("PERFORMANCE OBJECTIVES", []),
            "content": topic_data.get("CONTENT", []),
            "teacher_activities": topic_data.get("TEACHER ACTIVITIES", []),
            "student_activities": topic_data.get("STUDENTS ACTIVITIES", topic_data.get("PUPILS ACTIVITIES", [])),
            "resources": topic_data.get("TEACHING AND LEARNING RESOURCES", []),
            "topic_name": topic_data.get("TOPIC NAME", topic)
        }
        return result
        
    except Exception as e:
        # Catch file system or JSON errors
        return {"error": f"Error retrieving curriculum objectives: {str(e)}"}


# --- LLM Call Function ---

def _call_llm(prompt: str, max_tokens: int = 1200, temperature: float = 0.15) -> str:
    """Directly call the Gemini API using the global client."""
    print(f"🔥 _call_llm started with max_tokens={max_tokens}, temperature={temperature}")
    try:           
        # Ensure client is initialized
        print(f"🔑 Ensuring client is initialized...")
        client = _ensure_client()
        print(f"✅ Client initialized successfully")
        
        # Count tokens for safety (optional, but good practice to keep)
        print(f"🔢 Counting tokens for model: {LLM_MODEL}")
        token_response = client.models.count_tokens(
            model=LLM_MODEL, 
            contents=prompt
        )
        prompt_tokens = token_response.total_tokens
        
        # NOTE: Using a simple print here to log the token count for performance monitoring
        print(f"📊 Prompt token count for {LLM_MODEL}: {prompt_tokens}")

        if prompt_tokens > 500000: 
            print(f"❌ Prompt too large: {prompt_tokens} tokens")
            raise RuntimeError(f"Input too large: {prompt_tokens} tokens (Max 500k advisory limit).")

        print(f"🚀 Making API call to generate content...")
        print(f"🎛️ Config: temperature={temperature}, maxOutputTokens={max_tokens}")
        response = client.models.generate_content(
            model=LLM_MODEL, 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                maxOutputTokens=max_tokens
            )
        )
        print(f"✅ API call completed successfully")
        
        if response and response.text:
            print(f"📝 Response received, length: {len(response.text)} chars")
            print(f"🔍 Response preview: {response.text[:200]}...")
            return response.text.strip()
        else:
            # Handle cases where the API call succeeds but the model returns no text (e.g., blocked content)
            print(f"⚠️ Empty response from Gemini")
            print(f"🔍 Response object: {response}")
            print(f"🔍 Prompt feedback: {getattr(response, 'prompt_feedback', 'None')}")
            return json.dumps({"error": "Gemini returned empty response.", 
                               "feedback": str(getattr(response, 'prompt_feedback', 'None'))})
            
    except Exception as e:
        # Raise generic RuntimeError to be caught by generate_lesson_plan
        print(f"💥 Exception in _call_llm: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"📍 Full traceback: {traceback.format_exc()}")
        raise RuntimeError(f"Gemini API call failed: {str(e)}")


# --- Prompt Template (Unchanged) ---

PROMPT_TEMPLATE = """
You are a curriculum expert and instructional designer experienced in creating simple, practical lesson structures for low-resource learning environments.

Your job is to produce one clear, structured lesson plan JSON for the details below. Be concise, avoid commentary, and return **only valid JSON**.

CONTEXT (Curriculum objectives found):
{curriculum_context}

INPUT DETAILS:
- Level: {grade}
- Subject: {subject}
- Topic: {topic}
- Language: {language}
- Context summary: {classroom_context}
- Available materials/resources: {teacher_input}
- Output mode: {output_mode}

REQUIREMENTS:
1) Return only JSON with these exact keys:
   - title
   - objectives
   - learning_outcomes
   - introduction
   - activities
   - differentiation
   - materials
   - assessment
   - classroom_management
   - extension
   - low_data_version
   - notes
2) Write short, functional sentences suitable for local learning contexts.
3) Avoid any reference to personal, medical, political, or sensitive issues.
4) Focus on task-based, practical activities that use common, low-cost materials.
5) If {output_mode} == "short", limit the plan to minimal elements (1–2 objectives).
6) Ensure the plan is self-contained, neutral in tone, and instructional.
7) Use simple English and context-neutral examples (e.g., “use local objects,” “draw on board”).
8) Do not include markdown, explanations, or extra text—JSON only.

END PROMPT.
"""


# --- Main Logic ---

def generate_lesson_plan(
    subject: str,
    grade: str,
    topic: str,
    curriculum_context: Optional[str] = None,
    teacher_input: Optional[str] = None,
    language: str = "English",
    classroom_context: str = "rural",
    output_mode: str = "full",
) -> Dict:
    """
    Main entry point for the backend. Generates a lesson plan using Gemini.
    """
    
    print(f"🚀 LESSON PLAN GENERATION STARTED")
    print(f"📝 Input params: grade={grade}, subject={subject}, topic={topic}")
    print(f"🎯 Teacher input: {teacher_input}")
    print(f"🌍 Language: {language}, Context: {classroom_context}, Mode: {output_mode}")
    
    # 1) Get curriculum context
    print(f"📚 Getting curriculum context...")
    if curriculum_context is None:
        print(f"🔍 Fetching curriculum objectives for: {grade} -> {subject} -> {topic}")
        curriculum_objectives = get_curriculum_objectives(grade, subject, topic)
        print(f"📋 Curriculum objectives result: {type(curriculum_objectives)}")
        
        if "error" not in curriculum_objectives:
            print(f"✅ Curriculum objectives found successfully")
            # Format the curriculum context from the retrieved data
            context_parts = []
            
            if curriculum_objectives.get("topic_name"):
                context_parts.append(f"Topic: {curriculum_objectives['topic_name']}")
                
            if curriculum_objectives.get("objectives"):
                context_parts.append(f"Performance Objectives: {'; '.join(curriculum_objectives['objectives'])}")
                
            if curriculum_objectives.get("content"):
                content_str = '; '.join(curriculum_objectives['content'])
                if len(content_str) > 500:  # Truncate content if too long
                    content_str = content_str[:497] + "..."
                context_parts.append(f"Content: {content_str}")
                
            if curriculum_objectives.get("teacher_activities"):
                activities_str = '; '.join(curriculum_objectives['teacher_activities'])
                if len(activities_str) > 300:  # Truncate activities if too long
                    activities_str = activities_str[:297] + "..."
                context_parts.append(f"Teacher Activities: {activities_str}")
                
            curriculum_context = " | ".join(context_parts)
            print(f"📖 Curriculum context built: {len(curriculum_context)} chars")
        else:
            # If curriculum retrieval failed, use the error message as context
            error_msg = curriculum_objectives.get('error', 'unknown error')
            curriculum_context = f"(Curriculum error: {error_msg})"
            print(f"❌ Curriculum error: {error_msg}")
            print(f"🔄 Using error context: {curriculum_context}")
    
    # Sanitize curriculum_context length - hard cap to prevent API errors
    print(f"🧹 Sanitizing curriculum context...")
    if curriculum_context:
        curriculum_context = curriculum_context.strip()
        original_length = len(curriculum_context)
        if len(curriculum_context) > 4000:
            curriculum_context = curriculum_context[:3900] + " ... [truncated]"
            print(f"✂️ Truncated context from {original_length} to {len(curriculum_context)} chars")
        else:
            print(f"📏 Context length OK: {len(curriculum_context)} chars")
    else:
        curriculum_context = "(No curriculum context available)"
        print(f"⚠️ No curriculum context available, using default")
        
    # 2) Build Prompt
    print(f"🔨 Building prompt...")
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
    
    print(f"📝 Prompt built successfully, length: {len(prompt)} chars")
    
    # 3) Call the LLM
    print(f"🤖 Calling LLM...")
    try:
        llm_response_text = _call_llm(prompt, max_tokens=1200, temperature=0.15)
        print(f"✅ LLM call successful, response length: {len(llm_response_text)} chars")
    except RuntimeError as e:
        # Catch and structure the raised API error for the FastAPI endpoint
        print(f"❌ LLM call failed with RuntimeError: {str(e)}")
        return {"from_cache": False, "result": {"error": str(e)}}
    except Exception as e:
        print(f"💥 LLM call failed with unexpected error: {str(e)}")
        return {"from_cache": False, "result": {"error": f"Unexpected error: {str(e)}"}}

    # 4) Attempt to parse as JSON
    print(f"🔧 Parsing JSON response...")
    parsed = None
    try:
        parsed = json.loads(llm_response_text)
        print(f"✅ JSON parsing successful")
        print(f"📊 Parsed result keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
    except Exception as json_error:
        print(f"❌ Initial JSON parsing failed: {str(json_error)}")
        print(f"🔍 Attempting robust parsing...")
        # Robust parsing: Try to extract the first JSON object from the text
        match = re.search(r"(\{[\s\S]*\})", llm_response_text)
        if match:
            print(f"🎯 Found JSON pattern in response")
            try:
                parsed = json.loads(match.group(1))
                print(f"✅ Robust JSON parsing successful")
            except Exception as extract_error:
                # Parsing failed even after extraction
                print(f"💥 Robust parsing also failed: {str(extract_error)}")
                parsed = {"error": "LLM returned invalid JSON (extraction failed)", "raw": llm_response_text}
        else:
            # LLM returned non-JSON/non-parseable text
            print(f"🚫 No JSON pattern found in response")
            parsed = {"error": "LLM did not return JSON format", "raw": llm_response_text}

    # 5) Return the result
    print(f"🎉 Lesson plan generation completed")
    print(f"📤 Returning result with keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
    return {"from_cache": False, "result": parsed}
