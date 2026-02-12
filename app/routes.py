from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Client, CheckIn, Session, TrainingPlan

bp = Blueprint("main", __name__)

def parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

def parse_float(value: str):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None

def parse_int(value: str):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None

@bp.get("/")
def home():
    return redirect(url_for("main.clients_list"))

# --------------------------
# Clients
# --------------------------
@bp.get("/clients")
def clients_list():
    q = (request.args.get("q") or "").strip()
    query = Client.query
    if q:
        query = query.filter(Client.full_name.ilike(f"%{q}%"))
    clients = query.order_by(Client.full_name.asc()).all()

    return render_template("clients_list.html", clients=clients, q=q)

@bp.get("/clients/new")
def client_new():
    return render_template("client_form.html", mode="create", client=None)

@bp.post("/clients/new")
def client_create():
    full_name = (request.form.get("full_name") or "").strip()
    if not full_name:
        flash("Full name is required.", "error")
        return redirect(url_for("main.client_new"))

    c = Client(
        full_name=full_name,
        email=(request.form.get("email") or "").strip() or None,
        phone=(request.form.get("phone") or "").strip() or None,
        height_cm=parse_int(request.form.get("height_cm")),
        start_date=parse_date(request.form.get("start_date")) or date.today(),
        notes=(request.form.get("notes") or "").strip() or None,
    )
    db.session.add(c)
    db.session.commit()
    flash("Client created.", "success")
    return redirect(url_for("main.client_detail", client_id=c.id))

@bp.get("/clients/<int:client_id>")
def client_detail(client_id: int):
    client = Client.query.get_or_404(client_id)

    checkins = (CheckIn.query
                .filter_by(client_id=client.id)
                .order_by(CheckIn.date.desc())
                .all())

    sessions = (Session.query
                .filter_by(client_id=client.id)
                .order_by(Session.date.desc())
                .all())

    plans = (TrainingPlan.query
             .filter_by(client_id=client.id)
             .order_by(TrainingPlan.id.desc())
             .all())

    return render_template(
        "client_detail.html",
        client=client,
        checkins=checkins,
        sessions=sessions,
        plans=plans
    )

@bp.get("/clients/<int:client_id>/edit")
def client_edit(client_id: int):
    client = Client.query.get_or_404(client_id)
    return render_template("client_form.html", mode="edit", client=client)

@bp.post("/clients/<int:client_id>/edit")
def client_update(client_id: int):
    client = Client.query.get_or_404(client_id)

    full_name = (request.form.get("full_name") or "").strip()
    if not full_name:
        flash("Full name is required.", "error")
        return redirect(url_for("main.client_edit", client_id=client.id))

    client.full_name = full_name
    client.email = (request.form.get("email") or "").strip() or None
    client.phone = (request.form.get("phone") or "").strip() or None
    client.height_cm = parse_int(request.form.get("height_cm"))
    client.start_date = parse_date(request.form.get("start_date")) or client.start_date
    client.notes = (request.form.get("notes") or "").strip() or None

    db.session.commit()
    flash("Client updated.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))

@bp.post("/clients/<int:client_id>/delete")
def client_delete(client_id: int):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Client deleted.", "success")
    return redirect(url_for("main.clients_list"))

# --------------------------
# Check-ins
# --------------------------
@bp.get("/clients/<int:client_id>/checkins/new")
def checkin_new(client_id: int):
    client = Client.query.get_or_404(client_id)
    return render_template("checkin_form.html", mode="create", client=client, checkin=None)

@bp.post("/clients/<int:client_id>/checkins/new")
def checkin_create(client_id: int):
    client = Client.query.get_or_404(client_id)

    d = parse_date(request.form.get("date"))
    if not d:
        flash("Valid date is required.", "error")
        return redirect(url_for("main.checkin_new", client_id=client.id))

    checkin = CheckIn(
        client_id=client.id,
        date=d,
        weight_kg=parse_float(request.form.get("weight_kg")),
        bodyfat_pct=parse_float(request.form.get("bodyfat_pct")),
        waist_cm=parse_float(request.form.get("waist_cm")),
        notes=(request.form.get("notes") or "").strip() or None
    )
    db.session.add(checkin)
    db.session.commit()
    flash("Check-in added.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))

@bp.get("/checkins/<int:checkin_id>/edit")
def checkin_edit(checkin_id: int):
    checkin = CheckIn.query.get_or_404(checkin_id)
    client = Client.query.get_or_404(checkin.client_id)
    return render_template("checkin_form.html", mode="edit", client=client, checkin=checkin)

@bp.post("/checkins/<int:checkin_id>/edit")
def checkin_update(checkin_id: int):
    checkin = CheckIn.query.get_or_404(checkin_id)
    client = Client.query.get_or_404(checkin.client_id)

    d = parse_date(request.form.get("date"))
    if not d:
        flash("Valid date is required.", "error")
        return redirect(url_for("main.checkin_edit", checkin_id=checkin.id))

    checkin.date = d
    checkin.weight_kg = parse_float(request.form.get("weight_kg"))
    checkin.bodyfat_pct = parse_float(request.form.get("bodyfat_pct"))
    checkin.waist_cm = parse_float(request.form.get("waist_cm"))
    checkin.notes = (request.form.get("notes") or "").strip() or None

    db.session.commit()
    flash("Check-in updated.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))

@bp.post("/checkins/<int:checkin_id>/delete")
def checkin_delete(checkin_id: int):
    checkin = CheckIn.query.get_or_404(checkin_id)
    client_id = checkin.client_id
    db.session.delete(checkin)
    db.session.commit()
    flash("Check-in deleted.", "success")
    return redirect(url_for("main.client_detail", client_id=client_id))

# --------------------------
# Sessions
# --------------------------
@bp.get("/clients/<int:client_id>/sessions/new")
def session_new(client_id: int):
    client = Client.query.get_or_404(client_id)
    return render_template("session_form.html", mode="create", client=client, session_obj=None)

@bp.post("/clients/<int:client_id>/sessions/new")
def session_create(client_id: int):
    client = Client.query.get_or_404(client_id)

    d = parse_date(request.form.get("date"))
    if not d:
        flash("Valid date is required.", "error")
        return redirect(url_for("main.session_new", client_id=client.id))

    session_obj = Session(
        client_id=client.id,
        date=d,
        session_type=(request.form.get("session_type") or "").strip() or None,
        duration_min=parse_int(request.form.get("duration_min")),
        rpe=parse_int(request.form.get("rpe")),
        notes=(request.form.get("notes") or "").strip() or None
    )
    db.session.add(session_obj)
    db.session.commit()
    flash("Session added.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))

@bp.get("/sessions/<int:session_id>/edit")
def session_edit(session_id: int):
    session_obj = Session.query.get_or_404(session_id)
    client = Client.query.get_or_404(session_obj.client_id)
    return render_template("session_form.html", mode="edit", client=client, session_obj=session_obj)

@bp.post("/sessions/<int:session_id>/edit")
def session_update(session_id: int):
    session_obj = Session.query.get_or_404(session_id)
    client = Client.query.get_or_404(session_obj.client_id)

    d = parse_date(request.form.get("date"))
    if not d:
        flash("Valid date is required.", "error")
        return redirect(url_for("main.session_edit", session_id=session_obj.id))

    session_obj.date = d
    session_obj.session_type = (request.form.get("session_type") or "").strip() or None
    session_obj.duration_min = parse_int(request.form.get("duration_min"))
    session_obj.rpe = parse_int(request.form.get("rpe"))
    session_obj.notes = (request.form.get("notes") or "").strip() or None

    db.session.commit()
    flash("Session updated.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))

@bp.post("/sessions/<int:session_id>/delete")
def session_delete(session_id: int):
    session_obj = Session.query.get_or_404(session_id)
    client_id = session_obj.client_id
    db.session.delete(session_obj)
    db.session.commit()
    flash("Session deleted.", "success")
    return redirect(url_for("main.client_detail", client_id=client_id))

# --------------------------
# Training Plans
# --------------------------
@bp.get("/clients/<int:client_id>/plans/new")
def plan_new(client_id: int):
    client = Client.query.get_or_404(client_id)
    return render_template("plan_form.html", mode="create", client=client, plan=None)

@bp.post("/clients/<int:client_id>/plans/new")
def plan_create(client_id: int):
    client = Client.query.get_or_404(client_id)

    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Title is required.", "error")
        return redirect(url_for("main.plan_new", client_id=client.id))

    plan = TrainingPlan(
        client_id=client.id,
        title=title,
        goal=(request.form.get("goal") or "").strip() or None,
        start_date=parse_date(request.form.get("start_date")),
        end_date=parse_date(request.form.get("end_date")),
        plan_text=(request.form.get("plan_text") or "").strip() or None
    )
    db.session.add(plan)
    db.session.commit()
    flash("Plan added.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))

@bp.get("/plans/<int:plan_id>/edit")
def plan_edit(plan_id: int):
    plan = TrainingPlan.query.get_or_404(plan_id)
    client = Client.query.get_or_404(plan.client_id)
    return render_template("plan_form.html", mode="edit", client=client, plan=plan)

@bp.post("/plans/<int:plan_id>/edit")
def plan_update(plan_id: int):
    plan = TrainingPlan.query.get_or_404(plan_id)
    client = Client.query.get_or_404(plan.client_id)

    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Title is required.", "error")
        return redirect(url_for("main.plan_edit", plan_id=plan.id))

    plan.title = title
    plan.goal = (request.form.get("goal") or "").strip() or None
    plan.start_date = parse_date(request.form.get("start_date"))
    plan.end_date = parse_date(request.form.get("end_date"))
    plan.plan_text = (request.form.get("plan_text") or "").strip() or None

    db.session.commit()
    flash("Plan updated.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))

@bp.post("/plans/<int:plan_id>/delete")
def plan_delete(plan_id: int):
    plan = TrainingPlan.query.get_or_404(plan_id)
    client_id = plan.client_id
    db.session.delete(plan)
    db.session.commit()
    flash("Plan deleted.", "success")
    return redirect(url_for("main.client_detail", client_id=client_id))
