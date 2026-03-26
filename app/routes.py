from datetime import datetime, date
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

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


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access required.", "error")
            return redirect(url_for("main.admin_login"))
        return view_func(*args, **kwargs)
    return wrapper


def client_login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("client_id"):
            flash("Please log in to access your portal.", "error")
            return redirect(url_for("main.client_login"))
        return view_func(*args, **kwargs)
    return wrapper


# --------------------------
# Root
# --------------------------
@bp.get("/")
def home():
    return redirect(url_for("main.admin_login"))


# --------------------------
# Simple Admin Login
# --------------------------
@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        # Simple hardcoded admin login for v2
        if username == "admin" and password == "admin123":
            session.clear()
            session["is_admin"] = True
            flash("Welcome back, coach.", "success")
            return redirect(url_for("main.clients_list"))

        flash("Invalid admin credentials.", "error")
        return redirect(url_for("main.admin_login"))

    return render_template("admin_login.html")


@bp.get("/admin/logout")
def admin_logout():
    session.clear()
    flash("Admin logged out.", "success")
    return redirect(url_for("main.admin_login"))


# --------------------------
# Client Login
# --------------------------
@bp.route("/client/login", methods=["GET", "POST"])
def client_login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        client = Client.query.filter_by(username=username).first()

        if client and client.check_password(password):
            session.clear()
            session["client_id"] = client.id
            session["client_name"] = client.full_name
            flash("Logged in successfully.", "success")
            return redirect(url_for("main.client_dashboard"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("main.client_login"))

    return render_template("client_login.html")


@bp.get("/client/logout")
def client_logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.client_login"))


# --------------------------
# Admin / Coach Side
# --------------------------
@bp.get("/clients")
@admin_required
def clients_list():
    q = (request.args.get("q") or "").strip()
    query = Client.query

    if q:
        query = query.filter(Client.full_name.ilike(f"%{q}%"))

    clients = query.order_by(Client.full_name.asc()).all()
    return render_template("clients_list.html", clients=clients, q=q)


@bp.get("/clients/new")
@admin_required
def client_new():
    return render_template("client_form.html", mode="create", client=None)


@bp.post("/clients/new")
@admin_required
def client_create():
    full_name = (request.form.get("full_name") or "").strip()
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()

    if not full_name:
        flash("Full name is required.", "error")
        return redirect(url_for("main.client_new"))

    if not username:
        flash("Username is required.", "error")
        return redirect(url_for("main.client_new"))

    if not password:
        flash("Password is required.", "error")
        return redirect(url_for("main.client_new"))

    existing = Client.query.filter_by(username=username).first()
    if existing:
        flash("That username is already taken.", "error")
        return redirect(url_for("main.client_new"))

    client = Client(
        full_name=full_name,
        email=(request.form.get("email") or "").strip() or None,
        phone=(request.form.get("phone") or "").strip() or None,
        height_cm=parse_int(request.form.get("height_cm")),
        start_date=parse_date(request.form.get("start_date")) or date.today(),
        notes=(request.form.get("notes") or "").strip() or None,
        username=username,
    )
    client.set_password(password)

    db.session.add(client)
    db.session.commit()

    flash("Client created.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))


@bp.get("/clients/<int:client_id>")
@admin_required
def client_detail(client_id: int):
    client = Client.query.get_or_404(client_id)

    checkins = (
        CheckIn.query
        .filter_by(client_id=client.id)
        .order_by(CheckIn.date.desc())
        .all()
    )

    sessions = (
        Session.query
        .filter_by(client_id=client.id)
        .order_by(Session.date.desc())
        .all()
    )

    plans = (
        TrainingPlan.query
        .filter_by(client_id=client.id)
        .order_by(TrainingPlan.id.desc())
        .all()
    )

    return render_template(
        "client_detail.html",
        client=client,
        checkins=checkins,
        sessions=sessions,
        plans=plans
    )


@bp.get("/clients/<int:client_id>/edit")
@admin_required
def client_edit(client_id: int):
    client = Client.query.get_or_404(client_id)
    return render_template("client_form.html", mode="edit", client=client)


@bp.post("/clients/<int:client_id>/edit")
@admin_required
def client_update(client_id: int):
    client = Client.query.get_or_404(client_id)

    full_name = (request.form.get("full_name") or "").strip()
    username = (request.form.get("username") or "").strip()
    new_password = (request.form.get("password") or "").strip()

    if not full_name:
        flash("Full name is required.", "error")
        return redirect(url_for("main.client_edit", client_id=client.id))

    if not username:
        flash("Username is required.", "error")
        return redirect(url_for("main.client_edit", client_id=client.id))

    existing = Client.query.filter_by(username=username).first()
    if existing and existing.id != client.id:
        flash("That username is already taken.", "error")
        return redirect(url_for("main.client_edit", client_id=client.id))

    client.full_name = full_name
    client.email = (request.form.get("email") or "").strip() or None
    client.phone = (request.form.get("phone") or "").strip() or None
    client.height_cm = parse_int(request.form.get("height_cm"))
    client.start_date = parse_date(request.form.get("start_date")) or client.start_date
    client.notes = (request.form.get("notes") or "").strip() or None
    client.username = username

    if new_password:
        client.set_password(new_password)

    db.session.commit()

    flash("Client updated.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))


@bp.post("/clients/<int:client_id>/delete")
@admin_required
def client_delete(client_id: int):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Client deleted.", "success")
    return redirect(url_for("main.clients_list"))


# --------------------------
# Admin Check-ins
# --------------------------
@bp.get("/clients/<int:client_id>/checkins/new")
@admin_required
def checkin_new(client_id: int):
    client = Client.query.get_or_404(client_id)
    return render_template("checkin_form.html", mode="create", client=client, checkin=None)


@bp.post("/clients/<int:client_id>/checkins/new")
@admin_required
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
        notes=(request.form.get("notes") or "").strip() or None,
    )
    db.session.add(checkin)
    db.session.commit()

    flash("Check-in added.", "success")
    return redirect(url_for("main.client_detail", client_id=client.id))


@bp.get("/checkins/<int:checkin_id>/edit")
@admin_required
def checkin_edit(checkin_id: int):
    checkin = CheckIn.query.get_or_404(checkin_id)
    client = Client.query.get_or_404(checkin.client_id)
    return render_template("checkin_form.html", mode="edit", client=client, checkin=checkin)


@bp.post("/checkins/<int:checkin_id>/edit")
@admin_required
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
@admin_required
def checkin_delete(checkin_id: int):
    checkin = CheckIn.query.get_or_404(checkin_id)
    client_id = checkin.client_id
    db.session.delete(checkin)
    db.session.commit()

    flash("Check-in deleted.", "success")
    return redirect(url_for("main.client_detail", client_id=client_id))


# --------------------------
# Admin Sessions
# --------------------------
@bp.get("/clients/<int:client_id>/sessions/new")
@admin_required
def session_new(client_id: int):
    client = Client.query.get_or_404(client_id)
    return render_template("session_form.html", mode="create", client=client, session_obj=None)


@bp.post("/clients/<int:client_id>/sessions/new")
@admin_required
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
@admin_required
def session_edit(session_id: int):
    session_obj = Session.query.get_or_404(session_id)
    client = Client.query.get_or_404(session_obj.client_id)
    return render_template("session_form.html", mode="edit", client=client, session_obj=session_obj)


@bp.post("/sessions/<int:session_id>/edit")
@admin_required
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
@admin_required
def session_delete(session_id: int):
    session_obj = Session.query.get_or_404(session_id)
    client_id = session_obj.client_id
    db.session.delete(session_obj)
    db.session.commit()

    flash("Session deleted.", "success")
    return redirect(url_for("main.client_detail", client_id=client_id))


# --------------------------
# Admin Training Plans
# --------------------------
@bp.get("/clients/<int:client_id>/plans/new")
@admin_required
def plan_new(client_id: int):
    client = Client.query.get_or_404(client_id)
    return render_template("plan_form.html", mode="create", client=client, plan=None)


@bp.post("/clients/<int:client_id>/plans/new")
@admin_required
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
@admin_required
def plan_edit(plan_id: int):
    plan = TrainingPlan.query.get_or_404(plan_id)
    client = Client.query.get_or_404(plan.client_id)
    return render_template("plan_form.html", mode="edit", client=client, plan=plan)


@bp.post("/plans/<int:plan_id>/edit")
@admin_required
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
@admin_required
def plan_delete(plan_id: int):
    plan = TrainingPlan.query.get_or_404(plan_id)
    client_id = plan.client_id
    db.session.delete(plan)
    db.session.commit()

    flash("Plan deleted.", "success")
    return redirect(url_for("main.client_detail", client_id=client_id))


# --------------------------
# Client Portal
# --------------------------
@bp.get("/client/dashboard")
@client_login_required
def client_dashboard():
    client = Client.query.get_or_404(session["client_id"])

    checkins = (
        CheckIn.query
        .filter_by(client_id=client.id)
        .order_by(CheckIn.date.desc())
        .all()
    )

    sessions_list = (
        Session.query
        .filter_by(client_id=client.id)
        .order_by(Session.date.desc())
        .all()
    )

    plans = (
        TrainingPlan.query
        .filter_by(client_id=client.id)
        .order_by(TrainingPlan.id.desc())
        .all()
    )

    return render_template(
        "client_portal_dashboard.html",
        client=client,
        checkins=checkins,
        sessions=sessions_list,
        plans=plans
    )


@bp.route("/client/profile", methods=["GET", "POST"])
@client_login_required
def client_profile():
    client = Client.query.get_or_404(session["client_id"])

    if request.method == "POST":
        client.email = (request.form.get("email") or "").strip() or None
        client.phone = (request.form.get("phone") or "").strip() or None
        client.height_cm = parse_int(request.form.get("height_cm"))
        client.notes = (request.form.get("notes") or "").strip() or None

        new_password = (request.form.get("password") or "").strip()
        if new_password:
            client.set_password(new_password)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("main.client_profile"))

    return render_template("client_profile.html", client=client)


@bp.route("/client/checkins/new", methods=["GET", "POST"])
@client_login_required
def client_checkin_new():
    client = Client.query.get_or_404(session["client_id"])

    if request.method == "POST":
        d = parse_date(request.form.get("date"))
        if not d:
            flash("Valid date is required.", "error")
            return redirect(url_for("main.client_checkin_new"))

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

        flash("Check-in submitted.", "success")
        return redirect(url_for("main.client_dashboard"))

    return render_template("client_portal_checkin_form.html", client=client)