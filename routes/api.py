from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import and_

from models import Booking, BookingHistory, Machine, db


api_bp = Blueprint("api", __name__, url_prefix="/api")
ALLOWED_STATUSES = {"pending", "approved", "completed", "cancelled"}


def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_datetime(value, field_name):
    if not value:
        raise ValueError(f"{field_name} is required")

    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _booking_conflict(machine_id, start_time, end_time, booking_id=None):
    filters = [
        Booking.machine_id == machine_id,
        Booking.is_deleted.is_(False),
        Booking.status != "cancelled",
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    ]
    if booking_id is not None:
        filters.append(Booking.id != booking_id)
    return db.session.scalar(db.select(Booking.id).where(and_(*filters)).limit(1))


def _record_history(booking, action):
    db.session.add(BookingHistory(booking=booking, action=action, snapshot=booking.snapshot()))


@api_bp.get("/health")
def health():
    return {"status": "ok"}, 200


@api_bp.get("/machines")
@login_required
def list_machines():
    return jsonify([machine.to_dict() for machine in Machine.query.order_by(Machine.name).all()])


@api_bp.get("/bookings")
@login_required
def list_bookings():
    query = Booking.query.filter_by(is_deleted=False)

    start = request.args.get("start")
    end = request.args.get("end")
    machine_id = request.args.get("machine_id", type=int)

    if start:
        query = query.filter(Booking.end_time >= _parse_datetime(start, "start"))
    if end:
        query = query.filter(Booking.start_time <= _parse_datetime(end, "end"))
    if machine_id:
        query = query.filter_by(machine_id=machine_id)

    bookings = query.order_by(Booking.start_time.asc()).all()
    return jsonify([booking.to_dict(current_user.id) for booking in bookings])


@api_bp.post("/bookings")
@login_required
def create_booking():
    data = request.get_json(silent=True) or {}

    try:
        machine_id = int(data.get("machine_id"))
        start_time = _parse_datetime(data.get("start"), "start")
        end_time = _parse_datetime(data.get("end"), "end")
    except (TypeError, ValueError):
        return jsonify({"error": "invalid booking request payload"}), 400

    title = (data.get("title") or "").strip() or "機台使用申請"
    purpose = (data.get("purpose") or "").strip()
    status = (data.get("status") or "pending").strip().lower()

    if not purpose:
        return jsonify({"error": "purpose is required"}), 400
    if start_time >= end_time:
        return jsonify({"error": "start must be earlier than end"}), 400
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": "invalid status"}), 400

    machine = db.session.get(Machine, machine_id)
    if not machine:
        return jsonify({"error": "machine not found"}), 404
    if _booking_conflict(machine_id, start_time, end_time):
        return jsonify({"error": "booking conflict detected"}), 409

    booking = Booking(
        title=title,
        purpose=purpose,
        applicant_name=current_user.username,
        start_time=start_time,
        end_time=end_time,
        status=status,
        machine=machine,
        user_id=current_user.id,
    )
    db.session.add(booking)
    db.session.flush()
    _record_history(booking, "created")
    db.session.commit()
    return jsonify(booking.to_dict(current_user.id)), 201


@api_bp.put("/bookings/<int:booking_id>")
@login_required
def update_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.is_deleted:
        return jsonify({"error": "booking not found"}), 404
    if booking.user_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}

    try:
        machine_id = int(data.get("machine_id", booking.machine_id))
        start_time = _parse_datetime(data.get("start", booking.start_time.isoformat()), "start")
        end_time = _parse_datetime(data.get("end", booking.end_time.isoformat()), "end")
    except (TypeError, ValueError):
        return jsonify({"error": "invalid booking request payload"}), 400

    purpose = (data.get("purpose", booking.purpose) or "").strip()
    title = (data.get("title", booking.title) or "").strip() or booking.title
    status = (data.get("status", booking.status) or booking.status).strip().lower()

    if not purpose:
        return jsonify({"error": "purpose is required"}), 400
    if start_time >= end_time:
        return jsonify({"error": "start must be earlier than end"}), 400
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": "invalid status"}), 400

    machine = db.session.get(Machine, machine_id)
    if not machine:
        return jsonify({"error": "machine not found"}), 404
    if _booking_conflict(machine_id, start_time, end_time, booking.id):
        return jsonify({"error": "booking conflict detected"}), 409

    booking.machine = machine
    booking.title = title
    booking.purpose = purpose
    booking.start_time = start_time
    booking.end_time = end_time
    booking.status = status
    _record_history(booking, "updated")
    db.session.commit()
    return jsonify(booking.to_dict(current_user.id))


@api_bp.delete("/bookings/<int:booking_id>")
@login_required
def delete_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.is_deleted:
        return jsonify({"error": "booking not found"}), 404
    if booking.user_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    booking.is_deleted = True
    booking.deleted_at = _utc_now()
    booking.status = "cancelled"
    _record_history(booking, "deleted")
    db.session.commit()
    return jsonify({"message": "booking deleted"})


@api_bp.get("/bookings/<int:booking_id>/history")
@login_required
def booking_history(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "booking not found"}), 404
    if booking.user_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    return jsonify([entry.to_dict() for entry in booking.history])
