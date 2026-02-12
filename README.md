# Fitness Coaching Management App (CRUD)

A simple web app for fitness coaches to manage clients, progress check-ins, session history, and training plans.

## Features
- Clients: add / edit / delete
- Progress check-ins: track weight, body fat %, waist, notes
- Sessions: track session type, duration, RPE, notes
- Training plans: store a plan (title/goal/date range + text plan)
- Search clients

## Tech Stack
- Flask (Python)
- SQLite (SQLAlchemy)
- HTML + CSS

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python run.py
