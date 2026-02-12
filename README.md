# Fitness Coaching Management App (CRUD)

A full-stack web application built for fitness coaches to manage clients, track progress, log sessions, and manage training plans.

Designed as a real-world coaching management system using relational database design and a clean Flask architecture.

---

## 🚀 Features

### Client Management
- Create, edit, delete clients
- Store contact details, height, start date, and notes
- Search clients by name

### Progress Tracking
- Log check-ins (weight, body fat %, waist measurement)
- Store notes per check-in
- View check-ins in reverse chronological order

### Session History
- Track training sessions
- Log session type, duration, RPE, and notes

### Training Plans
- Create structured plans per client
- Store goal, date range, and detailed program text
- Manage plan history

---

## 🛠 Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** HTML + CSS
- **Architecture:** Application factory pattern with modular routes

---

## 📸 Screenshots

![Clients](docs/screenshots/clients.png)
![Dashboard](docs/screenshots/dashboard.png)

---

## ⚙️ Run Locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
