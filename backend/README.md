# Attendance Management System — Backend

REST API backend for managing student attendance, built with FastAPI and MongoDB.

## Architecture

```
FastAPI (REST API)
    ├── MongoDB (via Motor async driver)
    └── Ollama/Llama (optional AI assistant)
```

## Requirements

- Python 3.12+
- MongoDB (local or remote)
- Ollama (optional, for AI features)

## Installation

### 1. Create virtual environment

```bash
cd backend
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env
```

Edit `.env` and set:
- `JWT_SECRET_KEY` to a secure random string
- `MONGODB_URI` to your MongoDB connection string

### 4. Start MongoDB

Make sure MongoDB is running on `localhost:27017` or update `MONGODB_URI` in `.env`.

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` — Register new user
- `POST /api/v1/auth/login` — Login and get JWT
- `GET /api/v1/auth/me` — Get current user

### Students
- `GET /api/v1/students` — List students (supports filtering)
- `POST /api/v1/students` — Create student
- `GET /api/v1/students/{id}` — Get student
- `PUT /api/v1/students/{id}` — Update student
- `DELETE /api/v1/students/{id}` — Delete student

### Classes
- `GET /api/v1/classes` — List classes
- `POST /api/v1/classes` — Create class
- `GET /api/v1/classes/{id}` — Get class
- `PUT /api/v1/classes/{id}` — Update class
- `DELETE /api/v1/classes/{id}` — Delete class

### Subjects
- `GET /api/v1/subjects` — List subjects
- `POST /api/v1/subjects` — Create subject
- `GET /api/v1/subjects/{id}` — Get subject
- `PUT /api/v1/subjects/{id}` — Update subject
- `DELETE /api/v1/subjects/{id}` — Delete subject

### Attendance
- `POST /api/v1/attendance/sessions` — Create session
- `GET /api/v1/attendance/sessions` — List sessions
- `GET /api/v1/attendance/sessions/{id}` — Get session with records
- `POST /api/v1/attendance/sessions/{id}/records` — Mark single record
- `POST /api/v1/attendance/sessions/{id}/bulk` — Bulk mark attendance
- `PUT /api/v1/attendance/records/{id}` — Update record
- `GET /api/v1/attendance/student/{id}` — Student attendance records
- `GET /api/v1/attendance/student/{id}/summary` — Student attendance summary
- `GET /api/v1/attendance/class/{id}` — Class attendance records

### Reports
- `GET /api/v1/reports/daily` — Daily report
- `GET /api/v1/reports/monthly` — Monthly report
- `GET /api/v1/reports/student/{id}` — Student report
- `GET /api/v1/reports/class/{id}` — Class report

### Exports
- `GET /api/v1/exports/attendance/csv` — Export CSV
- `GET /api/v1/exports/attendance/excel` — Export Excel

### AI Assistant
- `POST /api/v1/ai/chat` — Chat with AI assistant

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## AI Assistant (Optional)

### Start Ollama

1. Install Ollama from https://ollama.ai
2. Pull a model:
   ```bash
   ollama pull llama3
   ```
3. Start Ollama:
   ```bash
   ollama serve
   ```
4. The AI endpoints will automatically use Ollama when available.

The core application works without Ollama.

## Project Structure

```
backend/
├── app/
│   ├── main.py           — Application entry point
│   ├── config.py         — Settings from .env
│   ├── database.py       — MongoDB connection
│   ├── core/             — Security, dependencies
│   ├── models/           — Data models
│   ├── schemas/          — Pydantic validation
│   ├── routers/          — API endpoints
│   ├── services/         — Business logic
│   ├── ai/               — AI assistant (isolated)
│   └── utils/            — Helpers
├── tests/                — Test suite
├── exports/              — Exported files
├── requirements.txt
├── .env
└── README.md
```
