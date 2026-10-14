"""All SQL lives here. Every query is parameterised (no string-built values)."""
import sqlite3
from typing import Optional

COLUMNS = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]


def _to_row(data: dict) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in data.items()}


def create_student(db: sqlite3.Connection, data: dict) -> dict:
    row = _to_row(data)
    cols = ", ".join(COLUMNS)
    marks = ", ".join(":" + c for c in COLUMNS)
    cur = db.execute(f"INSERT INTO students ({cols}) VALUES ({marks})", {c: row.get(c) for c in COLUMNS})
    db.commit()
    return get_student(db, cur.lastrowid)


def get_student(db: sqlite3.Connection, student_id: int) -> Optional[dict]:
    r = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(r) if r else None


def list_students(db, name=None, course=None, email=None, born_after=None, born_before=None,
                  skip: int = 0, limit: int = 100) -> list[dict]:
    sql, params = "SELECT * FROM students WHERE 1=1", []
    if name:
        sql += " AND name LIKE ?"; params.append(f"%{name}%")
    if course:
        sql += " AND course LIKE ?"; params.append(f"%{course}%")
    if email:
        sql += " AND email = ?"; params.append(email)
    if born_after:
        sql += " AND date_of_birth > ?"; params.append(born_after.isoformat())
    if born_before:
        sql += " AND date_of_birth < ?"; params.append(born_before.isoformat())
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    params += [limit, skip]
    return [dict(r) for r in db.execute(sql, params).fetchall()]


def count_students(db, **filters) -> int:
    return len(list_students(db, skip=0, limit=1_000_000, **filters))


def update_student(db, student_id: int, data: dict) -> Optional[dict]:
    row = _to_row(data)
    if not row:
        return get_student(db, student_id)
    sets = ", ".join(f"{k} = :{k}" for k in row)   # keys come from the validated model, never from user text
    row["_id"] = student_id
    cur = db.execute(f"UPDATE students SET {sets} WHERE id = :_id", row)
    db.commit()
    return get_student(db, student_id) if cur.rowcount else None


def delete_student(db, student_id: int) -> bool:
    cur = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    return cur.rowcount > 0
