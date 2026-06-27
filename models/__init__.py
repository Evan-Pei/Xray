from datetime import datetime, timezone

from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bookings = db.relationship("Booking", back_populates="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    bookings = db.relationship("Booking", back_populates="machine", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    applicant_name = db.Column(db.String(80), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
    machine_id = db.Column(db.Integer, db.ForeignKey("machine.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    machine = db.relationship("Machine", back_populates="bookings")
    user = db.relationship("User", back_populates="bookings")
    history = db.relationship(
        "BookingHistory",
        back_populates="booking",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="BookingHistory.changed_at",
    )

    def to_dict(self, current_user_id=None):
        return {
            "id": self.id,
            "title": self.title,
            "purpose": self.purpose,
            "applicant_name": self.applicant_name,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "status": self.status,
            "machine_id": self.machine_id,
            "machine_name": self.machine.name,
            "can_edit": current_user_id == self.user_id,
        }

    def snapshot(self):
        return {
            "id": self.id,
            "title": self.title,
            "purpose": self.purpose,
            "applicant_name": self.applicant_name,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "status": self.status,
            "machine_id": self.machine_id,
            "machine_name": self.machine.name,
            "is_deleted": self.is_deleted,
        }


class BookingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    snapshot = db.Column(db.JSON, nullable=False)

    booking = db.relationship("Booking", back_populates="history")

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "changed_at": self.changed_at.isoformat(),
            "snapshot": self.snapshot,
        }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
