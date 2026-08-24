from datetime import datetime

from flask import Blueprint, abort, render_template, request
from flask_login import current_user, login_required

from models import Booking, Machine, User, db

web_bp = Blueprint("web", __name__, url_prefix="/")


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _escape_like(value):
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@web_bp.route("/", methods=["GET"])
def index():
    machines = Machine.query.order_by(Machine.name.asc()).all()
    users = User.query.order_by(User.username.asc()).all()

    machine_id = request.args.get("machine_id", type=int)
    start_date_raw = (request.args.get("start_date") or "").strip()
    end_date_raw = (request.args.get("end_date") or "").strip()
    user_query = (request.args.get("user") or "").strip()
    search_performed = any([machine_id, start_date_raw, end_date_raw, user_query])

    bookings = []
    if search_performed:
        query = Booking.query.filter(Booking.is_deleted.is_(False))
        if machine_id:
            query = query.filter(Booking.machine_id == machine_id)

        start_date = _parse_date(start_date_raw)
        end_date = _parse_date(end_date_raw)
        if start_date:
            query = query.filter(Booking.end_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(Booking.start_time <= datetime.combine(end_date, datetime.max.time()))
        if user_query:
            escaped_user_query = _escape_like(user_query)
            query = query.filter(Booking.applicant_name.ilike(f"%{escaped_user_query}%", escape="\\"))

        bookings = query.order_by(Booking.start_time.asc()).all()

    return render_template(
        "index.html",
        machines=machines,
        users=users,
        bookings=bookings,
        search_performed=search_performed,
        selected_machine_id=machine_id,
        selected_start_date=start_date_raw,
        selected_end_date=end_date_raw,
        selected_user=user_query,
    )


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
    today = datetime.now().date()
    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        if not (1 <= month <= 12):
            raise ValueError("invalid month")
    except (ValueError, TypeError):
        year, month = today.year, today.month

    qualified_users = [
        {"id": user.id, "username": user.username}
        for user in User.query.filter_by(is_qualified=True).order_by(User.username.asc()).all()
    ]

    return render_template(
        "calendar.html",
        init_year=year,
        init_month=month,
        today_year=today.year,
        today_month=today.month,
        today_day=today.day,
        current_username=current_user.username,
        current_user_id=current_user.id,
        current_user_is_admin=current_user.is_admin(),
        current_user_is_qualified=current_user.is_qualified,
        qualified_users=qualified_users,
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
