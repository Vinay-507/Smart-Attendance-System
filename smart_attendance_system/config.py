import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    DATABASE_DIR = os.getenv("DATABASE_DIR", str(BASE_DIR / "database"))
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        str(Path(DATABASE_DIR) / "attendance.db"),
    )

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    EMBEDDING_FOLDER = os.getenv("EMBEDDING_FOLDER", str(BASE_DIR / "embeddings"))
    LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "20")) * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
