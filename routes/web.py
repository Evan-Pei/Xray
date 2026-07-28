import calendar
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from models import (
    Booking,
    Machine,
    MACHINE_STATUS_MAINTENANCE,
    MACHINE_STATUS_ONLINE,
    db,
)

web_bp = Blueprint("web", __name__, url_prefix="/")


def _build_time_options():
    return [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in range(0, 60, 10)]


def _is_valid_time_range(start_time: str, end_time: str, valid_times: list[str]) -> bool:
    return start_time in valid_times and end_time in valid_times and start_time < end_time


@web_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@web_bp.route("/dashboard", methods=["GET"])
def dashboard():
    today = date.today()

    machines = Machine.query.order_by(Machine.id.asc()).all()
    today_bookings = (
        Booking.query
        .filter_by(year=today.year, month=today.month, day=today.day)
        .order_by(Booking.start_time.asc())
        .all()
    )

    online_count = sum(1 for m in machines if m.status == MACHINE_STATUS_ONLINE)
    maintenance_count = sum(1 for m in machines if m.status == MACHINE_STATUS_MAINTENANCE)

    metrics = [
        {"label": "Active Machines", "value": online_count},
        {"label": "Scheduled Today", "value": len(today_bookings)},
        {"label": "Maintenance", "value": maintenance_count},
    ]

    return render_template("dashboard.html", metrics=metrics, machines=machines)


@web_bp.route("/calendar", methods=["GET"])
def calendar_view():
    today = date.today()
    year, month = today.year, today.month

    cal = calendar.monthcalendar(year, month)
    month_name = today.strftime("%B %Y")

    bookings = (
        Booking.query
        .filter_by(year=year, month=month)
        .order_by(Booking.day.asc(), Booking.start_time.asc())
        .all()
    )

    bookings_by_day: dict[int, list] = {}
    for booking in bookings:
        bookings_by_day.setdefault(booking.day, []).append(booking)

    machine_names = [m.name for m in Machine.query.order_by(Machine.name.asc()).all()]
    time_options = _build_time_options()

    edit_id = request.args.get("edit_id", type=int)
    edit_booking = db.session.get(Booking, edit_id) if edit_id else None
    month_days = calendar.monthrange(year, month)[1]

    selected_day = request.args.get("day", type=int)
    if selected_day is not None and not (1 <= selected_day <= month_days):
        selected_day = None

    return render_template(
        "calendar.html",
        cal=cal,
        month_name=month_name,
        today_day=today.day,
        bookings_by_day=bookings_by_day,
        machine_names=machine_names,
        time_options=time_options,
        edit_booking=edit_booking,
        month_days=month_days,
        selected_day=selected_day,
    )


@web_bp.route("/calendar/bookings", methods=["POST"])
def create_booking():
    day_str = request.form.get("day", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time = request.form.get("end_time", "").strip()
    machine = request.form.get("machine", "").strip()
    patient = request.form.get("patient", "").strip()

    today = date.today()
    year, month = today.year, today.month
    month_days = calendar.monthrange(year, month)[1]
    time_options = _build_time_options()

    if not (day_str.isdigit() and 1 <= int(day_str) <= month_days):
        flash(f"Please provide a valid day (1-{month_days}).", "error")
        return redirect(url_for("web.calendar_view"))

    if not machine or not patient:
        flash("Please provide machine and patient name.", "error")
        return redirect(url_for("web.calendar_view", day=int(day_str)))

    if not _is_valid_time_range(start_time, end_time, time_options):
        flash(
            "Please provide a valid start/end time in 10-minute increments, and ensure end time is after start time.",
            "error",
        )
        return redirect(url_for("web.calendar_view", day=int(day_str)))

    db.session.add(
        Booking(
            year=year,
            month=month,
            day=int(day_str),
            start_time=start_time,
            end_time=end_time,
            machine=machine,
            patient=patient,
        )
    )
    db.session.commit()
    flash("Booking created successfully.")
    return redirect(url_for("web.calendar_view", day=int(day_str)))


@web_bp.route("/calendar/bookings/<int:booking_id>/edit", methods=["POST"])
def edit_booking(booking_id: int):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        abort(404)

    day_str = request.form.get("day", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time = request.form.get("end_time", "").strip()
    machine = request.form.get("machine", "").strip()
    patient = request.form.get("patient", "").strip()

    today = date.today()
    month_days = calendar.monthrange(today.year, today.month)[1]
    time_options = _build_time_options()

    if not (day_str.isdigit() and 1 <= int(day_str) <= month_days):
        flash(f"Please provide a valid day (1-{month_days}).", "error")
        return redirect(url_for("web.calendar_view", edit_id=booking_id))

    if not machine or not patient:
        flash("Please provide machine and patient name.", "error")
        return redirect(url_for("web.calendar_view", edit_id=booking_id))

    if not _is_valid_time_range(start_time, end_time, time_options):
        flash(
            "Please provide a valid start/end time in 10-minute increments, and ensure end time is after start time.",
            "error",
        )
        return redirect(url_for("web.calendar_view", edit_id=booking_id))

    booking.year = today.year
    booking.month = today.month
    booking.day = int(day_str)
    booking.start_time = start_time
    booking.end_time = end_time
    booking.machine = machine
    booking.patient = patient
    db.session.commit()
    flash("Booking updated successfully.")
    return redirect(url_for("web.calendar_view", day=booking.day))


@web_bp.route("/calendar/bookings/<int:booking_id>/delete", methods=["POST"])
def delete_booking(booking_id: int):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        abort(404)

    day = booking.day
    db.session.delete(booking)
    db.session.commit()
    flash("Booking deleted successfully.")
    return redirect(url_for("web.calendar_view", day=day))
