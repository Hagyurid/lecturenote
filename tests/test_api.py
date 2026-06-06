from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_workflow():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True

    project = client.post("/projects", json={
        "title": "test lecture",
        "source_files": {"lecture": "slides.pdf"},
        "workflow_rules": {"storage": "local_sqlite"}
    })
    assert project.status_code == 200
    project_id = project.json()["project_id"]

    outline = client.post(f"/projects/{project_id}/outline", json={
        "sections": [
            {"index": 1, "title": "Unit 1", "slide_range": "p.1-5"},
            {"index": 2, "title": "Unit 2", "slide_range": "p.6-10"}
        ]
    })
    assert outline.status_code == 200

    next_section = client.get(f"/projects/{project_id}/next")
    assert next_section.status_code == 200
    assert next_section.json()["next_section"]["section_index"] == 1

    section = client.post(f"/projects/{project_id}/sections", json={
        "section_index": 1,
        "title": "Unit 1",
        "content_markdown": "# 1. Unit 1\n\n## 0. Study direction\n...",
        "study_direction": "Focus on definitions.",
        "quality_report": {"format": "ok"}
    })
    assert section.status_code == 200

    image = client.post(f"/projects/{project_id}/image-items", json={
        "image_items": [
            {
                "image_id": "IMG-001",
                "source_page": "p.2",
                "source_slide": "slide 2",
                "insert_position": "Unit 1 after 2-1",
                "method": "original_slide_full_no_crop",
                "crop_allowed": False,
                "purpose": "diagram"
            }
        ]
    })
    assert image.status_code == 200

    textbook = client.post(f"/projects/{project_id}/textbook-items", json={
        "textbook_items": [
            {
                "item_type": "textbook_support",
                "uncertain_part": "missing definition",
                "textbook_evidence": "chapter 1",
                "reflected_content": "[textbook support] definition",
                "source": "textbook",
                "status": "done"
            }
        ]
    })
    assert textbook.status_code == 200

    final_bundle = client.get(f"/projects/{project_id}/final-bundle")
    assert final_bundle.status_code == 200
    body = final_bundle.json()
    assert body["project"]["title"] == "test lecture"
    assert len(body["sections"]) == 1
    assert len(body["image_items"]) == 1
    assert len(body["textbook_items"]) == 1
