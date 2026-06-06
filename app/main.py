from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException

from app.config import ACTION_API_KEY
from app.db import create_project, fetch_all, get_next_section, init_db, insert_many, save_outline, save_section
from app.models import (
    CheckItemsSave,
    DesignItemsSave,
    ExamItemsSave,
    FormulaItemsSave,
    ImageItemsSave,
    OutlineSave,
    ProjectCreate,
    ProjectCreated,
    SectionSave,
    TextbookItemsSave,
)

app = FastAPI(
    title="LectureNote Local Action Server",
    version="1.0.0",
    description="Stores Custom GPT workflow state and generated lecture-note outputs in local SQLite.",
)

init_db()


def require_auth(authorization: Optional[str] = Header(default=None)):
    if not ACTION_API_KEY:
        return True
    expected = f"Bearer {ACTION_API_KEY}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid Action API key")
    return True


@app.get("/health")
def health():
    return {"ok": True, "service": "lecturenote-local-action-server"}


@app.post("/projects", response_model=ProjectCreated, dependencies=[Depends(require_auth)])
def create_project_endpoint(payload: ProjectCreate):
    return create_project(payload.title, payload.source_files, payload.workflow_rules)


@app.post("/projects/{project_id}/outline", dependencies=[Depends(require_auth)])
def save_outline_endpoint(project_id: str, payload: OutlineSave):
    return save_outline(project_id, [s.model_dump() for s in payload.sections])


@app.get("/projects/{project_id}/next", dependencies=[Depends(require_auth)])
def get_next_section_endpoint(project_id: str):
    section = get_next_section(project_id)
    if not section:
        return {"next_section": None, "message": "No pending section"}
    return {"next_section": section}


@app.post("/projects/{project_id}/sections", dependencies=[Depends(require_auth)])
def save_section_endpoint(project_id: str, payload: SectionSave):
    return save_section(project_id, payload.model_dump())


@app.post("/projects/{project_id}/image-items", dependencies=[Depends(require_auth)])
def save_image_items_endpoint(project_id: str, payload: ImageItemsSave):
    return insert_many(project_id, "image_items", [i.model_dump() for i in payload.image_items])


@app.post("/projects/{project_id}/textbook-items", dependencies=[Depends(require_auth)])
def save_textbook_items_endpoint(project_id: str, payload: TextbookItemsSave):
    return insert_many(project_id, "textbook_items", [i.model_dump() for i in payload.textbook_items])


@app.post("/projects/{project_id}/exam-items", dependencies=[Depends(require_auth)])
def save_exam_items_endpoint(project_id: str, payload: ExamItemsSave):
    return insert_many(project_id, "exam_items", [i.model_dump() for i in payload.exam_items])


@app.post("/projects/{project_id}/check-items", dependencies=[Depends(require_auth)])
def save_check_items_endpoint(project_id: str, payload: CheckItemsSave):
    return insert_many(project_id, "check_items", [i.model_dump() for i in payload.check_items])


@app.post("/projects/{project_id}/formula-items", dependencies=[Depends(require_auth)])
def save_formula_items_endpoint(project_id: str, payload: FormulaItemsSave):
    return insert_many(project_id, "formula_items", [i.model_dump() for i in payload.formula_items])


@app.post("/projects/{project_id}/design-items", dependencies=[Depends(require_auth)])
def save_design_items_endpoint(project_id: str, payload: DesignItemsSave):
    return insert_many(project_id, "design_items", [i.model_dump() for i in payload.design_items])


@app.get("/projects/{project_id}/final-bundle", dependencies=[Depends(require_auth)])
def final_bundle_endpoint(project_id: str):
    bundle = fetch_all(project_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Project not found")
    return bundle
