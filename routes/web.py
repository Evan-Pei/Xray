import calendar
from datetime import datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Booking, Machine, db

web_bp = Blueprint("web", __name__, url_prefix="/")


@web_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@web_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """Dashboard showing today's bookings and machines"""
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # Get bookings for today
    today_bookings = (
        Booking.query
        .filter(
            Booking.start_time >= today_start,
            Booking.end_time <= today_end,
            Booking.is_deleted == False,
        )
        .order_by(Booking.start_time.asc())
        .all()
    )

    machines = Machine.query.order_by(Machine.id.asc()).all()

    metrics = [
        {"label": "Total Machines", "value": len(machines)},
        {"label": "Bookings Today", "value": len(today_bookings)},
        {"label": "Pending Approvals", "value": sum(1 for b in today_bookings if b.status == "pending")},
    ]

    return render_template("dashboard.html", metrics=metrics, machines=machines, bookings=today_bookings)


@web_bp.route("/calendar", methods=["GET"])
@login_required
def calendar_view():
    """Calendar view showing all bookings"""
    try:
        # Get current month info
        today = datetime.now().date()
        month_name = today.strftime("%B %Y")
        year = today.year
        month = today.month
        
        # Get calendar grid for current month
        cal_obj = calendar.monthcalendar(year, month)
        
        # Get all non-deleted bookings
        bookings = (
            Booking.query
            .filter_by(is_deleted=False)
            .order_by(Booking.start_time.asc())
            .all()
        )
        
        # Group bookings by day for display
        bookings_by_day = {}
        for booking in bookings:
            day = booking.start_time.day
            if day not in bookings_by_day:
                bookings_by_day[day] = []
            bookings_by_day[day].append(booking)
        
        # Get machines for dropdown
        machines = Machine.query.order_by(Machine.name.asc()).all()
        machine_names = [m.name for m in machines]
        
        # Generate time options (hourly slots)
        time_options = [f"{h:02d}:00" for h in range(7, 23)]
        
        # Get number of days in month
        month_days = calendar.monthrange(year, month)[1]
        
        # Today's day number
        today_day = today.day
        
        return render_template(
            "calendar.html",
            cal=cal_obj,
            month_name=month_name,
            bookings=bookings,
            bookings_by_day=bookings_by_day,
            machines=machines,
            machine_names=machine_names,
            time_options=time_options,
            month_days=month_days,
            today_day=today_day,
        )
    except Exception as e:
        flash(f"Error loading calendar: {str(e)}", "error")
        return render_template(
            "calendar.html",
            cal=[],
            month_name="",
            bookings=[],
            bookings_by_day={},
            machines=[],
            machine_names=[],
            time_options=[],
            month_days=0,
            today_day=0,
        )


@web_bp.route("/bookings", methods=["GET"])
@login_required
def list_bookings():
    """List all bookings for current user"""
    user_bookings = (
        Booking.query
        .filter_by(user_id=current_user.id, is_deleted=False)
        .order_by(Booking.start_time.desc())
        .all()
    )
    return render_template("bookings.html", bookings=user_bookings)


@web_bp.route("/bookings/<int:booking_id>", methods=["GET"])
@login_required
def view_booking(booking_id: int):
    """View a specific booking"""
    booking = db.session.get(Booking, booking_id)
    if booking is None or booking.is_deleted:
        abort(404)
    if booking.user_id != current_user.id:
        abort(403)
    return render_template("booking_detail.html", booking=booking)
