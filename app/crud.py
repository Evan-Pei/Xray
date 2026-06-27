from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus
from app.schemas import BookingCreate, BookingUpdate

STATUS_COLORS = {
    BookingStatus.PENDING: "#f59e0b",
    BookingStatus.APPROVED: "#16a34a",
    BookingStatus.REJECTED: "#dc2626",
}


class BookingConflictError(ValueError):
    pass


class BookingNotFoundError(LookupError):
    pass


def _find_conflict(
    db: Session,
    *,
    machine_name: str,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: int | None = None,
) -> Booking | None:
    filters = [
        Booking.machine_name == machine_name,
        Booking.status != BookingStatus.REJECTED,
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    ]
    if exclude_booking_id is not None:
        filters.append(Booking.id != exclude_booking_id)

    return db.scalar(select(Booking).where(and_(*filters)).limit(1))


def list_bookings_for_month(db: Session, *, year: int, month: int) -> list[Booking]:
    month_start = datetime(year, month, 1)
    next_year = year + 1 if month == 12 else year
    next_month = 1 if month == 12 else month + 1
    month_end = datetime(next_year, next_month, 1)
    stmt = (
        select(Booking)
        .where(and_(Booking.start_time < month_end, Booking.end_time > month_start))
        .order_by(Booking.start_time, Booking.machine_name)
    )
    return list(db.scalars(stmt).all())


def list_all_bookings(db: Session) -> list[Booking]:
    return list(db.scalars(select(Booking).order_by(Booking.start_time)).all())


def get_booking(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise BookingNotFoundError(f"Booking {booking_id} not found")
    return booking


def create_booking(db: Session, booking_in: BookingCreate) -> Booking:
    conflict = _find_conflict(
        db,
        machine_name=booking_in.machine_name,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
    )
    if conflict:
        raise BookingConflictError("The selected machine is already booked for the requested time window")

    booking = Booking(**booking_in.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def update_booking(db: Session, booking_id: int, booking_in: BookingUpdate) -> Booking:
    booking = get_booking(db, booking_id)
    conflict = _find_conflict(
        db,
        machine_name=booking_in.machine_name,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        exclude_booking_id=booking_id,
    )
    if conflict:
        raise BookingConflictError("The selected machine is already booked for the requested time window")

    for field, value in booking_in.model_dump().items():
        setattr(booking, field, value)

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def delete_booking(db: Session, booking_id: int) -> None:
    booking = get_booking(db, booking_id)
    db.delete(booking)
    db.commit()


def serialize_calendar_event(booking: Booking) -> dict:
    return {
        "id": str(booking.id),
        "title": f"{booking.machine_name} · {booking.applicant_name}",
        "start": booking.start_time,
        "end": booking.end_time,
        "color": STATUS_COLORS[booking.status],
        "extendedProps": {
            "applicant_name": booking.applicant_name,
            "machine_name": booking.machine_name,
            "purpose": booking.purpose,
            "status": booking.status.value,
            "actual_start": booking.actual_start.isoformat() if booking.actual_start else None,
            "actual_end": booking.actual_end.isoformat() if booking.actual_end else None,
            "usage_notes": booking.usage_notes,
        },
    }
