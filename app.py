import os
import secrets

from flask import Flask, current_app

from config import Config
from models import Machine, User, db, login_manager
from routes.admin import admin_bp
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
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    with app.app_context():
        db.create_all()
        _seed_machines()
        _seed_admin_user()

    return app


def _seed_machines():
    if Machine.query.count():
        return

    db.session.add_all(
        [
            Machine(name="X-Ray 1", description="High-resolution X-ray machine"),
            Machine(name="X-Ray 2", description="Fast throughput X-ray machine"),
            Machine(name="CT Scanner", description="Computed tomography scanner"),
        ]
    )
    db.session.commit()


def _seed_admin_user():
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    existing_user = User.query.filter_by(username=admin_username).first()
    if existing_user:
        if not existing_user.is_qualified:
            existing_user.is_qualified = True
            db.session.commit()
        return

    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_password:
        if current_app.config.get("TESTING", False):
            admin_password = "admin123"
        else:
            admin_password = secrets.token_urlsafe(18)
            current_app.logger.warning(
                "ADMIN_PASSWORD is not set. Generated temporary admin password for local development: %s",
                admin_password,
            )

    user = User(username=admin_username, is_qualified=True)
    user.set_password(admin_password)
    db.session.add(user)
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
