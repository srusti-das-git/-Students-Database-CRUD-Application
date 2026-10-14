"""EWB Internship Project: Students Database CRUD API (FastAPI + SQLite)."""
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status

from . import ai, crud
from .database import get_db, init_db
from .schemas import AskRequest, AskResponse, StudentCreate, StudentOut, StudentUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Students Database API",
    description="CRUD for student records (FastAPI + SQLite) with an optional local-AI Q&A endpoint.",
    version="1.0.0",
    lifespan=lifespan,
)


def _or_404(student, student_id: int):
    if student is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Student {student_id} not found")
    return student


def _duplicate_email():
    return HTTPException(status.HTTP_409_CONFLICT, "A student with this email already exists")


@app.get("/", tags=["health"])
def root():
    return {"message": "Students API is running", "docs": "/docs"}


# ---------- CREATE ----------
@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED, tags=["students"])
def create_student(student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    try:
        return crud.create_student(db, student.model_dump())
    except sqlite3.IntegrityError:
        raise _duplicate_email()


# ---------- READ (list + filter) ----------
@app.get("/students", response_model=list[StudentOut], tags=["students"])
def list_students(
    name: Optional[str] = Query(None, description="Partial name match"),
    course: Optional[str] = Query(None, description="Partial course match"),
    email: Optional[str] = Query(None, description="Exact email"),
    born_after: Optional[date] = Query(None, description="DOB strictly after YYYY-MM-DD"),
    born_before: Optional[date] = Query(None, description="DOB strictly before YYYY-MM-DD"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
):
    return crud.list_students(db, name, course, email, born_after, born_before, skip, limit)


# ---------- READ (single) ----------
@app.get("/students/{student_id}", response_model=StudentOut, tags=["students"])
def get_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    return _or_404(crud.get_student(db, student_id), student_id)


# ---------- UPDATE ----------
@app.put("/students/{student_id}", response_model=StudentOut, tags=["students"])
def replace_student(student_id: int, student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    """Full update: every field is replaced (omitted optional fields become null)."""
    _or_404(crud.get_student(db, student_id), student_id)
    try:
        return _or_404(crud.update_student(db, student_id, student.model_dump()), student_id)
    except sqlite3.IntegrityError:
        raise _duplicate_email()


@app.patch("/students/{student_id}", response_model=StudentOut, tags=["students"])
def patch_student(student_id: int, changes: StudentUpdate, db: sqlite3.Connection = Depends(get_db)):
    """Partial update: only fields you send are changed."""
    current = _or_404(crud.get_student(db, student_id), student_id)
    data = changes.model_dump(exclude_unset=True)
    for required in ("name", "date_of_birth"):
        if required in data and data[required] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{required} cannot be null")
    if "name" in data:
        data["name"] = data["name"].strip()
    merged = {**current, **data}
    if not merged.get("email") and not merged.get("phone"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Student must keep at least one of email or phone")
    try:
        return _or_404(crud.update_student(db, student_id, data), student_id)
    except sqlite3.IntegrityError:
        raise _duplicate_email()


# ---------- DELETE ----------
@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["students"])
def delete_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_student(db, student_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Student {student_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- OPTIONAL BONUS: local AI ----------
@app.post("/ask", response_model=AskResponse, tags=["ai-bonus"])
def ask(body: AskRequest, db: sqlite3.Connection = Depends(get_db)):
    """Ask e.g. 'How many students are there?' or 'List students born after 2005'.
    The backend fetches the records; Ollama only phrases the answer."""
    context, rows, strategy = ai.build_context(db, body.question)
    try:
        answer = ai.ask_ollama(body.question, context)
    except ai.OllamaUnavailable as e:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"Ollama is not reachable ({e}). Start it with 'ollama serve' and run 'ollama pull {ai.OLLAMA_MODEL}'.",
        )
    return AskResponse(question=body.question, answer=answer, records_used=len(rows), context_strategy=strategy)
 