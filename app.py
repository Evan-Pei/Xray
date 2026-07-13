import os

from flask import Flask

from config import Config
from models import Machine, db, login_manager
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
        _seed_machines()

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


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
