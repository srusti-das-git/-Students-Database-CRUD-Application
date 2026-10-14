import json
import os
import re
import urllib.error
import urllib.request
from datetime import date

from . import crud

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_CONTEXT_ROWS = 50


class OllamaUnavailable(Exception):
    pass


def build_context(db, question: str) -> tuple[str, list[dict], str]:
    """Return (facts_text, rows, strategy). Pure backend logic, no LLM involved."""
    q = question.lower()
    total = crud.count_students(db)
    facts = [f"Total students in database: {total}."]
    filters, parts = {}, []

    m = re.search(r"born\s+(after|before|in)\s+(\d{4})", q)
    if m:
        word, year = m.group(1), int(m.group(2))
        if word == "after":      # born in a year later than <year>
            filters["born_after"] = date(year, 12, 31)
        elif word == "before":
            filters["born_before"] = date(year, 1, 1)
        else:                    # "in"
            filters["born_after"] = date(year - 1, 12, 31)
            filters["born_before"] = date(year + 1, 1, 1)
        parts.append(f"dob_filter:{word} {year}")

    m = re.search(r"course\s+(?:is\s+|in\s+|of\s+)?([a-z0-9 +#.\-]+?)\s*\??$", q)
    if m:
        filters["course"] = m.group(1).strip()
        parts.append(f"course_filter:{filters['course']}")

    rows = crud.list_students(db, limit=MAX_CONTEXT_ROWS, **filters)
    if filters:
        matched = crud.count_students(db, **filters)
        facts.append(f"Students matching the question's filter: {matched}.")
        if matched > MAX_CONTEXT_ROWS:
            facts.append(f"(Only the first {MAX_CONTEXT_ROWS} are listed below.)")

    lines = [
        f"- id={r['id']}, name={r['name']}, dob={r['date_of_birth']}, course={r['course']}, "
        f"email={r['email']}, enrolled={r['enrollment_date']}"
        for r in rows
    ]
    strategy = "+".join(parts) if parts else "all_students_sample"
    return "\n".join(facts + ["Records:"] + (lines or ["(none)"])), rows, strategy


def ask_ollama(question: str, context: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": (
                "You answer questions about a student database. Use ONLY the facts and "
                "records provided. Do not invent data. If the answer is not in the data, "
                "say you don't know. Be brief and clear.")},
            {"role": "user", "content": f"DATA:\n{context}\n\nQUESTION: {question}"},
        ],
    }
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
        raise OllamaUnavailable(str(e))
