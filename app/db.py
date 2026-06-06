import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from app.config import DATABASE_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source_files TEXT NOT NULL DEFAULT '{}',
                workflow_rules TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'in_progress',
                current_section_index INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS outline_sections (
                project_id TEXT NOT NULL,
                section_index INTEGER NOT NULL,
                title TEXT NOT NULL,
                slide_range TEXT NOT NULL DEFAULT '',
                transcript_range TEXT NOT NULL DEFAULT '',
                textbook_range TEXT NOT NULL DEFAULT '',
                exam_format_range TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                PRIMARY KEY (project_id, section_index)
            );

            CREATE TABLE IF NOT EXISTS sections (
                project_id TEXT NOT NULL,
                section_index INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                content_markdown TEXT NOT NULL,
                study_direction TEXT NOT NULL DEFAULT '',
                quality_report TEXT NOT NULL DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, section_index)
            );

            CREATE TABLE IF NOT EXISTS image_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                image_id TEXT NOT NULL,
                source_page TEXT NOT NULL DEFAULT '',
                source_slide TEXT NOT NULL DEFAULT '',
                insert_position TEXT NOT NULL DEFAULT '',
                method TEXT NOT NULL DEFAULT 'original_slide_full_no_crop',
                crop_allowed INTEGER NOT NULL DEFAULT 0,
                purpose TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                needs_review INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS textbook_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                item_type TEXT NOT NULL DEFAULT 'textbook_support',
                uncertain_part TEXT NOT NULL DEFAULT '',
                textbook_evidence TEXT NOT NULL DEFAULT '',
                reflected_content TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS exam_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                item_type TEXT NOT NULL DEFAULT 'exam_format_based',
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                confidence TEXT NOT NULL DEFAULT 'medium',
                note TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS check_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'open'
            );

            CREATE TABLE IF NOT EXISTS formula_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                location TEXT NOT NULL,
                formula_type TEXT NOT NULL DEFAULT '',
                check_content TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'open'
            );

            CREATE TABLE IF NOT EXISTS design_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                check_content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open'
            );
            """
        )


def create_project(title: str, source_files: Dict[str, Any], workflow_rules: Dict[str, Any]) -> Dict[str, Any]:
    project_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO projects (project_id, title, source_files, workflow_rules) VALUES (?, ?, ?, ?)",
            (project_id, title, json.dumps(source_files, ensure_ascii=False), json.dumps(workflow_rules, ensure_ascii=False)),
        )
    return {"project_id": project_id, "title": title, "status": "in_progress"}


def save_outline(project_id: str, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    with get_conn() as conn:
        conn.execute("DELETE FROM outline_sections WHERE project_id = ?", (project_id,))
        for s in sections:
            conn.execute(
                """
                INSERT INTO outline_sections (
                    project_id, section_index, title, slide_range, transcript_range,
                    textbook_range, exam_format_range, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    s.get("index"),
                    s.get("title", ""),
                    s.get("slide_range", ""),
                    s.get("transcript_range", ""),
                    s.get("textbook_range", ""),
                    s.get("exam_format_range", ""),
                    s.get("status", "pending"),
                ),
            )
    return {"ok": True, "section_count": len(sections)}


def get_next_section(project_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM outline_sections
            WHERE project_id = ? AND status != 'done'
            ORDER BY section_index ASC
            LIMIT 1
            """,
            (project_id,),
        ).fetchone()
    return dict(row) if row else None


def save_section(project_id: str, section: Dict[str, Any]) -> Dict[str, Any]:
    idx = section["section_index"]
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO sections (
                project_id, section_index, title, content_markdown, study_direction, quality_report
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                idx,
                section.get("title", ""),
                section["content_markdown"],
                section.get("study_direction", ""),
                json.dumps(section.get("quality_report", {}), ensure_ascii=False),
            ),
        )
        conn.execute(
            "UPDATE outline_sections SET status = 'done' WHERE project_id = ? AND section_index = ?",
            (project_id, idx),
        )
    return {"ok": True, "saved_section_index": idx}


def insert_many(project_id: str, table: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {"ok": True, "saved_count": 0}

    allowed = {
        "image_items": ["image_id", "source_page", "source_slide", "insert_position", "method", "crop_allowed", "purpose", "note", "needs_review"],
        "textbook_items": ["item_type", "uncertain_part", "textbook_evidence", "reflected_content", "source", "status"],
        "exam_items": ["item_type", "content", "source", "confidence", "note"],
        "check_items": ["item_type", "content", "source", "status"],
        "formula_items": ["location", "formula_type", "check_content", "status"],
        "design_items": ["rule_type", "check_content", "status"],
    }
    if table not in allowed:
        raise ValueError("Invalid table")

    cols = allowed[table]
    placeholders = ",".join(["?"] * (len(cols) + 1))
    col_sql = ",".join(["project_id"] + cols)

    with get_conn() as conn:
        for row in rows:
            values = [project_id] + [row.get(c, False if c in ("crop_allowed", "needs_review") else "") for c in cols]
            values = [int(v) if isinstance(v, bool) else v for v in values]
            conn.execute(f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})", values)

    return {"ok": True, "saved_count": len(rows)}


def fetch_all(project_id: str) -> Dict[str, Any]:
    with get_conn() as conn:
        project = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
        if not project:
            return {}

        def rows(table: str, order: str = "id ASC") -> List[Dict[str, Any]]:
            return [dict(r) for r in conn.execute(f"SELECT * FROM {table} WHERE project_id = ? ORDER BY {order}", (project_id,)).fetchall()]

        outline = [dict(r) for r in conn.execute(
            "SELECT * FROM outline_sections WHERE project_id = ? ORDER BY section_index ASC",
            (project_id,),
        ).fetchall()]

        sections = [dict(r) for r in conn.execute(
            "SELECT * FROM sections WHERE project_id = ? ORDER BY section_index ASC",
            (project_id,),
        ).fetchall()]

    p = dict(project)
    p["source_files"] = json.loads(p.get("source_files") or "{}")
    p["workflow_rules"] = json.loads(p.get("workflow_rules") or "{}")

    for s in sections:
        s["quality_report"] = json.loads(s.get("quality_report") or "{}")

    return {
        "project": p,
        "outline": outline,
        "sections": sections,
        "image_items": rows("image_items"),
        "textbook_items": rows("textbook_items"),
        "exam_items": rows("exam_items"),
        "check_items": rows("check_items"),
        "formula_items": rows("formula_items"),
        "design_items": rows("design_items"),
    }
