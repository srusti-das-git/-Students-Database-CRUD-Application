"""Insert DUMMY students for demo/testing.  Run from project root:  python -m scripts.seed"""
from datetime import date

from app import crud
from app.database import _connect, init_db

DUMMY = [
    ("Aarav Sharma", "2004-03-15", "aarav@example.com",  "+91 90000 00001", "Python Backend",  "2024-07-01"),
    ("Diya Patel",   "2006-08-22", "diya@example.com",   "+91 90000 00002", "Data Science",    "2024-07-01"),
    ("Rohan Mishra", "2005-12-05", "rohan@example.com",  None,             "Python Backend",  "2024-08-10"),
    ("Sneha Das",    "2007-01-30", "sneha@example.com",  "+91 90000 00004", "Web Development", "2025-01-15"),
    ("Kabir Nayak",  "2003-06-18", None,                 "+91 90000 00005", "Data Science",    "2023-07-01"),
    ("Ananya Rout",  "2006-11-11", "ananya@example.com", "+91 90000 00006", "Python Backend",  "2025-01-15"),
]

if __name__ == "__main__":
    init_db()
    db = _connect()
    added = 0
    for name, dob, email, phone, course, enrolled in DUMMY:
        if email and db.execute("SELECT 1 FROM students WHERE email = ?", (email,)).fetchone():
            continue
        crud.create_student(db, dict(
            name=name, date_of_birth=date.fromisoformat(dob), email=email, phone=phone,
            course=course, address="Dummy Address", enrollment_date=date.fromisoformat(enrolled)))
        added += 1
    print(f"Seeded {added} dummy students.")
