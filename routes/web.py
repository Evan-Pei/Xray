import calendar
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from models import Booking, Machine, db

web_bp = Blueprint('web', __name__, url_prefix='/')

# ---------------------------------------------------------------------------
# Mock data used by the dashboard view
# ---------------------------------------------------------------------------

_MACHINES = [
    {"name": "X-Ray 1",    "description": "High-resolution X-ray machine",  "status": "online"},
    {"name": "X-Ray 2",    "description": "Fast throughput X-ray machine",   "status": "maintenance"},
    {"name": "CT Scanner", "description": "Computed tomography scanner",      "status": "online"},
]


@web_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@web_bp.route('/dashboard', methods=['GET'])
def dashboard():
    online_count = sum(1 for m in _MACHINES if m['status'] == 'online')
    metrics = [
        {"label": "Active Machines",   "value": online_count},
        {"label": "Scheduled Today",   "value": 12},
        {"label": "Pending Requests",  "value": 4},
    ]
    return render_template('dashboard.html', metrics=metrics, machines=_MACHINES)


@web_bp.route('/calendar', methods=['GET'])
def calendar_view():
    today = date.today()
    year, month = today.year, today.month

    # Build a list-of-weeks; each week is a list of day numbers (0 = padding)
    cal = calendar.monthcalendar(year, month)
    month_name = today.strftime('%B %Y')

    # Load bookings for the current month from the database
    bookings = Booking.query.filter_by(year=year, month=month).order_by(Booking.time).all()
    bookings_by_day: dict[int, list] = {}
    for b in bookings:
        bookings_by_day.setdefault(b.day, []).append(b)

    machine_names = [m.name for m in Machine.query.order_by(Machine.name).all()]

    edit_id = request.args.get('edit_id', type=int)
    edit_booking = db.session.get(Booking, edit_id) if edit_id else None
    month_days = calendar.monthrange(year, month)[1]

    return render_template(
        'calendar.html',
        cal=cal,
        month_name=month_name,
        today_day=today.day,
        bookings_by_day=bookings_by_day,
        machine_names=machine_names,
        edit_booking=edit_booking,
        month_days=month_days,
    )


@web_bp.route('/calendar/bookings', methods=['POST'])
def create_booking():
    day_str = request.form.get('day', '').strip()
    time_str = request.form.get('time', '').strip()
    machine = request.form.get('machine', '').strip()
    patient = request.form.get('patient', '').strip()

    today = date.today()
    year, month = today.year, today.month
    month_days = calendar.monthrange(year, month)[1]

    if not (day_str.isdigit() and 1 <= int(day_str) <= month_days) or not time_str or not machine or not patient:
        flash(f"Please provide a valid day (1-{month_days}), time, machine, and patient name.", "error")
        return redirect(url_for('web.calendar_view'))

    db.session.add(Booking(
        year=year, month=month, day=int(day_str),
        time=time_str, machine=machine, patient=patient,
    ))
    db.session.commit()
    flash("Booking created successfully.")
    return redirect(url_for('web.calendar_view'))


@web_bp.route('/calendar/bookings/<int:booking_id>/edit', methods=['POST'])
def edit_booking(booking_id: int):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        abort(404)

    day_str = request.form.get('day', '').strip()
    time_str = request.form.get('time', '').strip()
    machine = request.form.get('machine', '').strip()
    patient = request.form.get('patient', '').strip()

    today = date.today()
    year, month = today.year, today.month
    month_days = calendar.monthrange(year, month)[1]

    if not (day_str.isdigit() and 1 <= int(day_str) <= month_days) or not time_str or not machine or not patient:
        flash(f"Please provide a valid day (1-{month_days}), time, machine, and patient name.", "error")
        return redirect(url_for('web.calendar_view', edit_id=booking_id))

    booking.day = int(day_str)
    booking.time = time_str
    booking.machine = machine
    booking.patient = patient
    db.session.commit()
    flash("Booking updated successfully.")
    return redirect(url_for('web.calendar_view'))


@web_bp.route('/calendar/bookings/<int:booking_id>/delete', methods=['POST'])
def delete_booking(booking_id: int):
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        abort(404)
    db.session.delete(booking)
    db.session.commit()
    flash("Booking deleted.")
    return redirect(url_for('web.calendar_view'))
