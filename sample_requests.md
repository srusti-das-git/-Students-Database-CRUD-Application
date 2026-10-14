# Sample Requests (cURL)

Start the FastAPI server first:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8081
```

Server URL: `http://127.0.0.1:8081`

## 1. Create a Student (POST)

```bash
curl -X POST http://127.0.0.1:8081/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Meera Jena","date_of_birth":"2005-04-12","email":"meera@example.com","phone":"+91 98765 43210","course":"Python Backend"}'
```

## 2. Read Students (GET)

List all students:

```bash
curl http://127.0.0.1:8081/students
```

Filter by course and date of birth:

```bash
curl "http://127.0.0.1:8081/students?course=Python&born_after=2005-12-31"
```

Filter by name:

```bash
curl "http://127.0.0.1:8081/students?name=Aarav"
```

Get a student by ID:

```bash
curl http://127.0.0.1:8081/students/1
```

List students with pagination:

```bash
curl "http://127.0.0.1:8081/students?skip=0&limit=10"
```

## 3. Update a Student

### Partial Update (PATCH)

Update only the course:

```bash
curl -X PATCH http://127.0.0.1:8081/students/1 \
  -H "Content-Type: application/json" \
  -d '{"course":"Data Science"}'
```

### Full Update (PUT)

Replace a student's details. Include all required fields for your API schema:

```bash
curl -X PUT http://127.0.0.1:8081/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Aarav Sharma","date_of_birth":"2004-03-15","email":"aarav@example.com","phone":"9876543210","course":"Computer Science","address":"Bhubaneswar, Odisha","enrollment_date":"2026-10-12"}'
```

## 4. Delete a Student (DELETE)

```bash
curl -X DELETE http://127.0.0.1:8081/students/1
```

A successful deletion should return `204 No Content`.

## 5. Error Handling

### Student Not Found (404)

```bash
curl http://127.0.0.1:8081/students/999999
```

Expected: `404 Not Found`.

### Invalid Input (422)

```bash
curl -X POST http://127.0.0.1:8081/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Student","date_of_birth":"not-a-date","email":"test@example.com"}'
```

Expected: `422 Unprocessable Entity`.

### Duplicate Email (409)

Use an email address that already exists in the database:

```bash
curl -X POST http://127.0.0.1:8081/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Another Student","date_of_birth":"2005-05-10","email":"existing@example.com"}'
```

Expected: `409 Conflict`, provided that `existing@example.com` is already registered.

## 6. Optional AI Extension (Ollama)

The Ollama service must be running, and the configured model must be installed.

Ask a question about student records:

```bash
curl -X POST http://127.0.0.1:8081/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"How many students are there?"}'
```

Ask about students born after 2005:

```bash
curl -X POST http://127.0.0.1:8081/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"List students born after 2005"}'
```

## Notes

- Replace student ID `1` with an ID that actually exists in your database.
- Use dummy student information when testing.
- The AI endpoint is optional; the CRUD API does not require Ollama.
- Interactive testing is also available at `http://127.0.0.1:8081/docs`.
