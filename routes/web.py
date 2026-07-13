import calendar
from datetime import date, datetime, time

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from models import Booking, MACHINE_STATUSES, Machine, db


web_bp = Blueprint("web", __name__, url_prefix="/")


def _machine_form_values(machine=None):
    if machine is None:
        return {"name": "", "description": "", "status": MACHINE_STATUSES[0]}

    return {
        "name": machine.name,
        "description": machine.description,
        "status": machine.status,
    }


def _booking_form_values(booking=None):
    if booking is None:
        return {"booking_date": "", "booking_time": "", "machine_id": "", "patient": ""}

    return {
        "booking_date": booking.booking_date.isoformat(),
        "booking_time": booking.booking_time.strftime("%H:%M"),
        "machine_id": str(booking.machine_id),
        "patient": booking.patient,
    }


def _render_machine_admin(machine=None, form_values=None, status_code=200):
    machines = Machine.query.order_by(Machine.name).all()
    return render_template(
        "admin_machines.html",
        machines=machines,
        machine=machine,
        form_values=form_values or _machine_form_values(machine),
        statuses=MACHINE_STATUSES,
    ), status_code


def _render_booking_admin(booking=None, form_values=None, status_code=200):
    bookings = Booking.query.order_by(Booking.booking_date, Booking.booking_time).all()
    machines = Machine.query.order_by(Machine.name).all()
    return render_template(
        "admin_bookings.html",
        bookings=bookings,
        booking=booking,
        machines=machines,
        form_values=form_values or _booking_form_values(booking),
    ), status_code


def _validate_machine_form(machine=None):
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    status = request.form.get("status", "").strip()
    form_values = {"name": name, "description": description, "status": status}

    if not name:
        flash("Machine name is required.", "error")
        return None, form_values
    if not description:
        flash("Machine description is required.", "error")
        return None, form_values
    if status not in MACHINE_STATUSES:
        flash("Machine status must be online, maintenance, or offline.", "error")
        return None, form_values

    existing = Machine.query.filter(Machine.name == name)
    if machine is not None:
        existing = existing.filter(Machine.id != machine.id)
    if existing.first():
        flash("Machine name must be unique.", "error")
        return None, form_values

    return (
        {"name": name, "description": description, "status": status},
        form_values,
    )


def _validate_booking_form():
    booking_date_raw = request.form.get("booking_date", "").strip()
    booking_time_raw = request.form.get("booking_time", "").strip()
    patient = request.form.get("patient", "").strip()
    machine_id_raw = request.form.get("machine_id", "").strip()

    form_values = {
        "booking_date": booking_date_raw,
        "booking_time": booking_time_raw,
        "patient": patient,
        "machine_id": machine_id_raw,
    }

    if not booking_date_raw:
        flash("Booking date is required.", "error")
        return None, form_values
    if not booking_time_raw:
        flash("Booking time is required.", "error")
        return None, form_values
    if not patient:
        flash("Patient name is required.", "error")
        return None, form_values

    try:
        booking_date = datetime.strptime(booking_date_raw, "%Y-%m-%d").date()
    except ValueError:
        flash("Booking date must use YYYY-MM-DD.", "error")
        return None, form_values

    try:
        booking_time = time.fromisoformat(booking_time_raw)
    except ValueError:
        flash("Booking time must use HH:MM.", "error")
        return None, form_values

    try:
        machine_id = int(machine_id_raw)
    except ValueError:
        flash("Please choose a valid machine.", "error")
        return None, form_values

    machine = db.session.get(Machine, machine_id)
    if machine is None:
        flash("Please choose a valid machine.", "error")
        return None, form_values

    return (
        {
            "booking_date": booking_date,
            "booking_time": booking_time,
            "patient": patient,
            "machine": machine,
        },
        form_values,
    )


@web_bp.route("/")
def index():
    return render_template("index.html")


@web_bp.route("/dashboard")
def dashboard():
    machines = Machine.query.order_by(Machine.name).all()
    online_count = sum(1 for machine in machines if machine.status == "online")
    today = date.today()
    scheduled_today = Booking.query.filter(Booking.booking_date == today).count()
    metrics = [
        {"label": "Active Machines", "value": online_count},
        {"label": "Scheduled Today", "value": scheduled_today},
        {"label": "Pending Requests", "value": 0},
    ]
    return render_template("dashboard.html", metrics=metrics, machines=machines)


@web_bp.route("/calendar")
def calendar_view():
    today = date.today()
    year, month = today.year, today.month
    last_day = calendar.monthrange(year, month)[1]
    cal = calendar.monthcalendar(year, month)
    month_name = today.strftime("%B %Y")

    bookings = (
        Booking.query.filter(
            Booking.booking_date >= date(year, month, 1),
            Booking.booking_date <= date(year, month, last_day),
        )
        .order_by(Booking.booking_date, Booking.booking_time)
        .all()
    )

    bookings_by_day = {}
    for booking in bookings:
        bookings_by_day.setdefault(booking.booking_date.day, []).append(booking)

    return render_template(
        "calendar.html",
        cal=cal,
        month_name=month_name,
        today_day=today.day,
        bookings_by_day=bookings_by_day,
    )


@web_bp.route("/admin/machines")
def machine_admin():
    return _render_machine_admin()


@web_bp.route("/admin/machines", methods=["POST"])
def machine_create():
    machine_data, form_values = _validate_machine_form()
    if machine_data is None:
        return _render_machine_admin(form_values=form_values, status_code=400)

    db.session.add(Machine(**machine_data))
    db.session.commit()
    flash("Machine saved.", "success")
    return redirect(url_for("web.machine_admin"))


@web_bp.route("/admin/machines/<int:machine_id>/edit")
def machine_edit(machine_id):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)
    return _render_machine_admin(machine=machine)


@web_bp.route("/admin/machines/<int:machine_id>/edit", methods=["POST"])
def machine_update(machine_id):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)
    machine_data, form_values = _validate_machine_form(machine=machine)
    if machine_data is None:
        return _render_machine_admin(machine=machine, form_values=form_values, status_code=400)

    machine.name = machine_data["name"]
    machine.description = machine_data["description"]
    machine.status = machine_data["status"]
    db.session.commit()
    flash("Machine updated.", "success")
    return redirect(url_for("web.machine_admin"))


@web_bp.route("/admin/machines/<int:machine_id>/delete", methods=["POST"])
def machine_delete(machine_id):
    machine = db.session.get(Machine, machine_id)
    if machine is None:
        abort(404)
    db.session.delete(machine)
    db.session.commit()
    flash("Machine deleted.", "success")
    return redirect(url_for("web.machine_admin"))


@web_bp.route("/admin/bookings")
def booking_admin():
    return _render_booking_admin()


@web_bp.route("/admin/bookings", methods=["POST"])
def booking_create():
    booking_data, form_values = _validate_booking_form()
    if booking_data is None:
        return _render_booking_admin(form_values=form_values, status_code=400)

    db.session.add(
        Booking(
            booking_date=booking_data["booking_date"],
            booking_time=booking_data["booking_time"],
            patient=booking_data["patient"],
            machine=booking_data["machine"],
        )
    )
    db.session.commit()
    flash("Booking saved.", "success")
    return redirect(url_for("web.booking_admin"))


@web_bp.route("/admin/bookings/<int:booking_id>/edit")
def booking_edit(booking_id):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        abort(404)
    return _render_booking_admin(booking=booking)


@web_bp.route("/admin/bookings/<int:booking_id>/edit", methods=["POST"])
def booking_update(booking_id):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        abort(404)
    booking_data, form_values = _validate_booking_form()
    if booking_data is None:
        return _render_booking_admin(booking=booking, form_values=form_values, status_code=400)

    booking.booking_date = booking_data["booking_date"]
    booking.booking_time = booking_data["booking_time"]
    booking.patient = booking_data["patient"]
    booking.machine = booking_data["machine"]
    db.session.commit()
    flash("Booking updated.", "success")
    return redirect(url_for("web.booking_admin"))


@web_bp.route("/admin/bookings/<int:booking_id>/delete", methods=["POST"])
def booking_delete(booking_id):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        abort(404)
    db.session.delete(booking)
    db.session.commit()
    flash("Booking deleted.", "success")
    return redirect(url_for("web.booking_admin"))
