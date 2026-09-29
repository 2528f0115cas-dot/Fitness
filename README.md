# FitBuddy – AI Fitness Plan Generator

A complete FastAPI + Jinja2 + SQLite application based on the supplied FitBuddy project specification. It generates personalized 7-day workout plans, goal-aligned nutrition/recovery tips, and AI-refined plans from feedback.

## What is included

- FastAPI web application and REST API
- Jinja2 pages: home, result, admin dashboard
- SQLAlchemy + SQLite persistence
- Gemini integration through the current `google-genai` SDK
- Structured Pydantic output for workout plans
- Feedback-based plan regeneration
- Nutrition/recovery tip generation
- Admin dashboard with delete action protected by an admin token
- Deterministic demo mode when Gemini is disabled or no key is configured
- Automated API/database tests
- Responsive frontend with no external frontend build step

## Architecture

`Browser → FastAPI routes → service layer → Gemini / demo provider → SQLAlchemy → SQLite`

The original document calls for Gemini 1.5 Pro for workout generation and Gemini Flash for nutrition. Those model IDs/SDK are historical; this implementation keeps the same roles but makes model IDs configurable and defaults to currently documented Gemini models. Google currently documents the `google-genai` Python SDK and structured JSON/Pydantic output.

## Safety note

FitBuddy is a wellness planning demo, not medical diagnosis or treatment. AI-generated exercise and nutrition suggestions should be reviewed by a qualified professional when appropriate. The app does not calculate medical nutrition prescriptions.

## Quick start – Windows PowerShell

```powershell
cd FitBuddy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GEMINI_API_KEY` for live AI. For a no-key demo, set `AI_ENABLED=false`.

Run:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 and API docs at http://127.0.0.1:8000/docs.

## Quick start – macOS/Linux

```bash
cd FitBuddy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env
uvicorn app.main:app --reload
```

## API endpoints

- `GET /api/health` – health check
- `POST /api/generate-workout` – create user + generate plan and tip
- `POST /api/submit-feedback` – regenerate a plan from feedback
- `GET /api/users` – list users/plans (admin token required)
- `GET /api/users/{user_id}` – retrieve one user/plan
- `DELETE /api/users/{user_id}` – delete a user (admin token required)

### API examples

Generate:

```bash
curl -X POST http://127.0.0.1:8000/api/generate-workout \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo01","name":"Alex","age":24,"weight":70,"goal":"muscle gain","intensity":"medium"}'
```

Update:

```bash
curl -X POST http://127.0.0.1:8000/api/submit-feedback \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo01","feedback":"Include more cardio and one extra recovery day."}'
```

Admin:

```bash
curl http://127.0.0.1:8000/api/users -H "X-Admin-Token: change-me"
```

## Testing

```bash
pytest -q
```

Tests run with Gemini disabled and therefore do not require an API key.

## VS Code

1. Open the `FitBuddy` folder.
2. Install the Microsoft Python extension.
3. Select `.venv` as the Python interpreter.
4. Copy `.env.example` to `.env`.
5. Use the integrated terminal to install dependencies and run Uvicorn.
6. Open `/docs` to exercise the REST API.

## Project tree

```text
FitBuddy/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── schemas.py
│   └── services/
│       ├── __init__.py
│       ├── gemini_generator.py
│       ├── gemini_flash_generator.py
│       └── updated_plan.py
├── static/
│   └── styles.css
├── templates/
│   ├── index.html
│   ├── result.html
│   └── all_users.html
├── tests/
│   └── test_app.py
├── data/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
