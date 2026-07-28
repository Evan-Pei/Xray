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
        # Get all non-deleted bookings, ordered by start time
        bookings = (
            Booking.query
            .filter_by(is_deleted=False)
            .order_by(Booking.start_time.asc())
            .all()
        )

        machines = Machine.query.order_by(Machine.name.asc()).all()

        return render_template(
            "calendar.html",
            bookings=bookings,
            machines=machines,
        )
    except Exception as e:
        flash(f"Error loading calendar: {str(e)}", "error")
        return render_template("calendar.html", bookings=[], machines=[])


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
