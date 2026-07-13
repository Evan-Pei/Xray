from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
login_manager = LoginManager()

MACHINE_STATUSES = ("online", "maintenance", "offline")


class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="online")
    bookings = db.relationship(
        "Booking",
        back_populates="machine",
        cascade="all, delete-orphan",
        order_by="Booking.booking_date, Booking.booking_time",
    )


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_date = db.Column(db.Date, nullable=False, index=True)
    booking_time = db.Column(db.Time, nullable=False)
    patient = db.Column(db.String(120), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey("machine.id"), nullable=False)
    machine = db.relationship("Machine", back_populates="bookings")


@login_manager.request_loader
def load_user_from_request(_request):
    return None
