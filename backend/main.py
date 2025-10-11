from fastapi import FastAPI
from pydantic import BaseModel
from core.curriculum_loader import get_curriculum_objectives
from core.lesson_generator import generate_lesson_plan

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

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "KlassIQ backend is running smoothly."}

@app.get("/get-subjects")
def get_subjects():
    # Example data; will later load dynamically from curriculum JSON
    return {"Primary 4": ["Mathematics", "English", "Basic Science", "Social Studies"]}

@app.post("/generate-plan")
def generate_plan(req: LessonRequest):
    objectives = get_curriculum_objectives(req.grade, req.subject, req.topic)
    plan = generate_lesson_plan(req.topic, objectives, req.teacher_input)
    return {
        "grade": req.grade,
        "subject": req.subject,
        "topic": req.topic,
        "objectives": objectives,
        "lesson_plan": plan
    }
