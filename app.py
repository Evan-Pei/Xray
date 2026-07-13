import os
from datetime import date, time

from flask import Flask

from config import Config
from models import Booking, Machine, db, login_manager
from routes.api import api_bp
from routes.auth import auth_bp
from routes.web import web_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    seeded_machines = [
        {
            "name": "X-Ray 1",
            "description": "High-resolution X-ray machine",
            "status": "online",
        },
        {
            "name": "X-Ray 2",
            "description": "Fast throughput X-ray machine",
            "status": "maintenance",
        },
        {
            "name": "CT Scanner",
            "description": "Computed tomography scanner",
            "status": "online",
        },
    ]
    machines_by_name = {machine.name: machine for machine in Machine.query.all()}
    if not machines_by_name:
        db.session.add_all(Machine(**machine) for machine in seeded_machines)
        db.session.flush()
        machines_by_name = {machine.name: machine for machine in Machine.query.all()}

    if Booking.query.count():
        db.session.commit()
        return

    today = date.today()
    db.session.add_all(
        [
            Booking(
                booking_date=date(today.year, today.month, 14),
                booking_time=time.fromisoformat("09:00"),
                machine_id=machines_by_name["X-Ray 1"].id,
                patient="Patient A",
            ),
            Booking(
                booking_date=date(today.year, today.month, 14),
                booking_time=time.fromisoformat("11:30"),
                machine_id=machines_by_name["CT Scanner"].id,
                patient="Patient B",
            ),
            Booking(
                booking_date=date(today.year, today.month, 15),
                booking_time=time.fromisoformat("08:30"),
                machine_id=machines_by_name["X-Ray 1"].id,
                patient="Patient C",
            ),
            Booking(
                booking_date=date(today.year, today.month, 16),
                booking_time=time.fromisoformat("14:00"),
                machine_id=machines_by_name["X-Ray 2"].id,
                patient="Patient D",
            ),
            Booking(
                booking_date=date(today.year, today.month, 17),
                booking_time=time.fromisoformat("10:00"),
                machine_id=machines_by_name["CT Scanner"].id,
                patient="Patient E",
            ),
            Booking(
                booking_date=date(today.year, today.month, 21),
                booking_time=time.fromisoformat("09:30"),
                machine_id=machines_by_name["X-Ray 1"].id,
                patient="Patient F",
            ),
            Booking(
                booking_date=date(today.year, today.month, 22),
                booking_time=time.fromisoformat("13:00"),
                machine_id=machines_by_name["X-Ray 2"].id,
                patient="Patient G",
            ),
        ]
    )
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
