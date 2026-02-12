from datetime import date
from app import db

class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    height_cm = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text, nullable=True)

    checkins = db.relationship("CheckIn", backref="client", cascade="all, delete-orphan", lazy=True)
    sessions = db.relationship("Session", backref="client", cascade="all, delete-orphan", lazy=True)
    plans = db.relationship("TrainingPlan", backref="client", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<Client {self.id} {self.full_name}>"

class CheckIn(db.Model):
    __tablename__ = "checkins"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    weight_kg = db.Column(db.Float, nullable=True)
    bodyfat_pct = db.Column(db.Float, nullable=True)
    waist_cm = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<CheckIn {self.id} client={self.client_id} date={self.date}>"

class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    session_type = db.Column(db.String(80), nullable=True)
    duration_min = db.Column(db.Integer, nullable=True)
    rpe = db.Column(db.Integer, nullable=True)  # 1-10
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Session {self.id} client={self.client_id} date={self.date}>"

class TrainingPlan(db.Model):
    __tablename__ = "training_plans"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    goal = db.Column(db.String(200), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    plan_text = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<TrainingPlan {self.id} client={self.client_id} title={self.title}>"
