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

    # OAuth configuration (optional)
    OAUTH_ENABLED = os.environ.get("OAUTH_ENABLED", "false").lower() == "true"
    OAUTH_PROVIDER = os.environ.get("OAUTH_PROVIDER", "frore")
    OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET", "")
    OAUTH_AUTHORIZE_URL = os.environ.get("OAUTH_AUTHORIZE_URL", "")
    OAUTH_TOKEN_URL = os.environ.get("OAUTH_TOKEN_URL", "")
    OAUTH_USERINFO_URL = os.environ.get("OAUTH_USERINFO_URL", "")
    OAUTH_REDIRECT_URI = os.environ.get("OAUTH_REDIRECT_URI", "")
    OAUTH_SCOPE = os.environ.get("OAUTH_SCOPE", "openid email profile")
