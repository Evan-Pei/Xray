import os
from datetime import timedelta


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Base configuration"""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

    _database_url = os.environ.get("DATABASE_URL", "sqlite:///xray.db")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(_database_url)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=7)