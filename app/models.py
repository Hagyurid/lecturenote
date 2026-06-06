from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(..., description="Project title")
    source_files: Dict[str, Any] = Field(default_factory=dict)
    workflow_rules: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreated(BaseModel):
    project_id: str
    title: str
    status: str


class OutlineSection(BaseModel):
    index: int
    title: str
    slide_range: str = ""
    transcript_range: str = ""
    textbook_range: str = ""
    exam_format_range: str = ""
    status: str = "pending"


class OutlineSave(BaseModel):
    sections: List[OutlineSection]


class SectionSave(BaseModel):
    section_index: int
    title: str = ""
    content_markdown: str
    study_direction: str = ""
    quality_report: Dict[str, Any] = Field(default_factory=dict)


class ImageItem(BaseModel):
    image_id: str
    source_page: str = ""
    source_slide: str = ""
    insert_position: str = ""
    method: str = "original_slide_full_no_crop"
    crop_allowed: bool = False
    purpose: str = ""
    note: str = ""
    needs_review: bool = False


class ImageItemsSave(BaseModel):
    image_items: List[ImageItem]


class TextbookItem(BaseModel):
    item_type: str = "textbook_support"
    uncertain_part: str = ""
    textbook_evidence: str = ""
    reflected_content: str = ""
    source: str = ""
    status: str = ""


class TextbookItemsSave(BaseModel):
    textbook_items: List[TextbookItem]


class ExamItem(BaseModel):
    item_type: str = "exam_format_based"
    content: str
    source: str = ""
    confidence: str = "medium"
    note: str = ""


class ExamItemsSave(BaseModel):
    exam_items: List[ExamItem]


class CheckItem(BaseModel):
    item_type: str
    content: str
    source: str = ""
    status: str = "open"


class CheckItemsSave(BaseModel):
    check_items: List[CheckItem]


class FormulaItem(BaseModel):
    location: str
    formula_type: str = ""
    check_content: str = ""
    status: str = "open"


class FormulaItemsSave(BaseModel):
    formula_items: List[FormulaItem]


class DesignItem(BaseModel):
    rule_type: str
    check_content: str
    status: str = "open"


class DesignItemsSave(BaseModel):
    design_items: List[DesignItem]
