"""Uygulama yapılandırması. Tüm hassas değerler ortam değişkenlerinden okunur."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    INSTANCE_DIR = BASE_DIR / "instance"

    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    # DATABASE_URL verilmezse yerel SQLite dosyası kullanılır (kurulumsuz çalışır).
    # MySQL örneği: mysql+pymysql://kullanici:parola@localhost:3306/yoklama_db
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{INSTANCE_DIR / 'yoklama.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # kamera karesi için 5 MB yeterli

    # Yüz tanıma (Facenet standart kosinüs eşiği 0.40'tır)
    FACE_MATCH_THRESHOLD = float(os.environ.get("FACE_MATCH_THRESHOLD") or "0.40")
    MIN_FACE_SIZE = int(os.environ.get("MIN_FACE_SIZE") or "60")  # piksel

    ALLOW_TEACHER_REGISTRATION = _env_bool("ALLOW_TEACHER_REGISTRATION", True)
    AUTO_CREATE_TABLES = True


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    AUTO_CREATE_TABLES = False
