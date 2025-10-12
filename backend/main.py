from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from core.lesson_generator import get_curriculum_objectives, generate_lesson_plan

app = FastAPI(
    title="KlassIQ API",
    description="KlassIQ is an AI-assisted lesson design API that helps teachers generate curriculum-aligned lesson plans for Nigeria’s 2025 basic education reform.",
    version="1.0.0"
)

class LessonRequest(BaseModel):
    grade: str
    subject: str
    topic: str
    term: str | None = None
    teacher_input: str | None = None
    
class CurriculumRequest(BaseModel):
    grade: str
    subject: str
    topic: str

@app.get("/health")
def health_check():
    """Health check with curriculum data verification."""
    try:
        curriculum_path = Path(__file__).resolve().parent / "data" / "curriculum_map.json"
        curriculum_exists = curriculum_path.exists()
        
        health_info = {
            "status": "ok", 
            "message": "KlassIQ backend is running smoothly.",
            "curriculum_map_exists": curriculum_exists
        }
        
        if curriculum_exists:
            try:
                with open(curriculum_path, 'r', encoding='utf-8') as f:
                    curriculum_data = json.load(f)
                health_info["curriculum_grades"] = len(curriculum_data)
                health_info["curriculum_subjects"] = sum(len(subjects) for subjects in curriculum_data.values())
            except Exception as e:
                health_info["curriculum_load_error"] = str(e)
        else:
            health_info["curriculum_path"] = str(curriculum_path)
            
        return health_info
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}"
        }


@app.get("/debug/test-curriculum")
def test_curriculum():
    """Debug endpoint to test curriculum functionality."""
    try:
        # Test getting grades
        grades_result = get_grades()
        
        if not grades_result.get("grades"):
            return {"error": "No grades found"}
            
        test_grade = grades_result["grades"][0]
        
        # Test getting subjects
        subjects_result = get_subjects_for_grade(test_grade)
        
        if not subjects_result.get("subjects"):
            return {"error": f"No subjects found for {test_grade}"}
            
        test_subject = subjects_result["subjects"][0]
        
        # Test curriculum objectives
        curriculum_result = get_curriculum_objectives(test_grade, test_subject, "test")
        
        return {
            "status": "success",
            "test_grade": test_grade,
            "test_subject": test_subject,
            "available_grades": len(grades_result["grades"]),
            "available_subjects": len(subjects_result["subjects"]),
            "curriculum_test": type(curriculum_result).__name__,
            "has_objectives": "objectives" in curriculum_result
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.get("/get-subjects")
def get_subjects():
    """Get available subjects for each grade level."""
    try:
        curriculum_path = Path(__file__).resolve().parent / "data" / "curriculum_map.json"
        
        if not curriculum_path.exists():
            raise HTTPException(status_code=500, detail="Curriculum map not found")
            
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            curriculum_data = json.load(f)
        
        subjects_by_grade = {}
        for grade, subjects in curriculum_data.items():
            subjects_by_grade[grade] = list(subjects.keys())
            
        return subjects_by_grade
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading subjects: {str(e)}")


@app.get("/curriculum/{grade}/{subject}/topics")
def get_topics(grade: str, subject: str):
    """Get available topics for a specific grade and subject."""
    try:
        import json
        from pathlib import Path
        
        curriculum_path = Path(__file__).resolve().parent / "data" / "curriculum_map.json"
        
        if not curriculum_path.exists():
            raise HTTPException(status_code=500, detail="Curriculum map not found")
            
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            curriculum_data = json.load(f)
        
        if grade not in curriculum_data:
            available_grades = list(curriculum_data.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Grade '{grade}' not found. Available grades: {available_grades}"
            )
            
        grade_data = curriculum_data[grade]
        
        if subject not in grade_data:
            available_subjects = list(grade_data.keys())
            raise HTTPException(
                status_code=404,
                detail=f"Subject '{subject}' not found in {grade}. Available subjects: {available_subjects}"
            )
            
        subject_data = grade_data[subject]
        
        # Extract all topics from the curriculum structure
        topics = []
        
        def extract_topics_recursive(data):
            """Recursively extract all topic names from curriculum structure."""
            if isinstance(data, dict):
                if "TOPICS" in data and isinstance(data["TOPICS"], list):
                    for topic_item in data["TOPICS"]:
                        if isinstance(topic_item, dict) and "TOPIC NAME" in topic_item:
                            topics.append(topic_item["TOPIC NAME"])
                            
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        extract_topics_recursive(value)
                        
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, (dict, list)):
                        extract_topics_recursive(item)
        
        extract_topics_recursive(subject_data)
        
        return {
            "grade": grade,
            "subject": subject,
            "topics": sorted(list(set(topics)))  # Remove duplicates and sort
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting topics: {str(e)}")


@app.post("/curriculum")
def get_curriculum_topic_data(req: CurriculumRequest):
    """Get curriculum objectives, content, and activities for a specific topic."""
    try:
        curriculum_data = get_curriculum_objectives(req.grade, req.subject, req.topic)
        
        if "error" in curriculum_data:
            raise HTTPException(status_code=404, detail=curriculum_data["error"])
            
        return {
            "grade": req.grade,
            "subject": req.subject,
            "topic": req.topic,
            "curriculum_data": curriculum_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving curriculum data: {str(e)}")


@app.post("/generate-plan")
def generate_plan(req: LessonRequest):
    """Generate a lesson plan based on curriculum objectives."""
    try:
        print(f"DEBUG: Received lesson plan request - Grade: {req.grade}, Subject: {req.subject}, Topic: {req.topic}")
        
        # Check if curriculum file exists
        curriculum_path = Path(__file__).resolve().parent / "data" / "curriculum_map.json"
        if not curriculum_path.exists():
            print(f"ERROR: Curriculum map not found at {curriculum_path}")
            raise HTTPException(status_code=500, detail=f"Curriculum map not found at {curriculum_path}")
        
        print("DEBUG: Curriculum map file exists")
        
        # Test curriculum objectives retrieval first
        try:
            curriculum_objectives = get_curriculum_objectives(req.grade, req.subject, req.topic)
            print(f"DEBUG: Curriculum objectives retrieved: {type(curriculum_objectives)}")
            if "error" in curriculum_objectives:
                print(f"DEBUG: Curriculum retrieval error: {curriculum_objectives['error']}")
        except Exception as e:
            print(f"ERROR: Failed to retrieve curriculum objectives: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Curriculum retrieval failed: {str(e)}")
        
        # Generate the lesson plan (this will auto-retrieve curriculum objectives)
        print("DEBUG: Starting lesson plan generation...")
        result = generate_lesson_plan(
            subject=req.subject,
            grade=req.grade,
            topic=req.topic,
            teacher_input=req.teacher_input
        )
        
        print(f"DEBUG: Lesson plan generation completed. Result type: {type(result)}")
        
        if not result:
            raise HTTPException(status_code=500, detail="Lesson plan generation returned empty result")
            
        if "error" in result.get("result", {}):
            error_detail = result["result"]["error"]
            print(f"ERROR: Lesson generation error: {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)
            
        response = {
            "grade": req.grade,
            "subject": req.subject,
            "topic": req.topic,
            "lesson_plan": result.get("result"),
            "from_cache": result.get("from_cache", False)
        }
        
        print("DEBUG: Successfully created response")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error generating lesson plan: {str(e)}"
        print(f"FATAL ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


# Additional utility endpoints
@app.get("/curriculum/grades")
def get_grades():
    """Get all available grade levels."""
    try:
        import json
        from pathlib import Path
        
        curriculum_path = Path(__file__).resolve().parent / "data" / "curriculum_map.json"
        
        if not curriculum_path.exists():
            raise HTTPException(status_code=500, detail="Curriculum map not found")
            
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            curriculum_data = json.load(f)
            
        return {
            "grades": list(curriculum_data.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading grades: {str(e)}")


@app.get("/curriculum/{grade}/subjects")  
def get_subjects_for_grade(grade: str):
    """Get available subjects for a specific grade."""
    try:
        import json
        from pathlib import Path
        
        curriculum_path = Path(__file__).resolve().parent / "data" / "curriculum_map.json"
        
        if not curriculum_path.exists():
            raise HTTPException(status_code=500, detail="Curriculum map not found")
            
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            curriculum_data = json.load(f)
        
        if grade not in curriculum_data:
            available_grades = list(curriculum_data.keys())
            raise HTTPException(
                status_code=404,
                detail=f"Grade '{grade}' not found. Available grades: {available_grades}"
            )
            
        return {
            "grade": grade,
            "subjects": list(curriculum_data[grade].keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading subjects: {str(e)}")
