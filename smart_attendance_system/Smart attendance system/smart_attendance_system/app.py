import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, render_template

from config import Config
from database.db import close_db, init_db
from routes.api import api_bp
from routes.attendance import attendance_bp
from routes.reports import reports_bp
from routes.students import students_bp
from services.report_service import ReportService


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    _ensure_runtime_directories(app)
    _configure_logging(app)

    app.teardown_appcontext(close_db)
    app.register_blueprint(api_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(students_bp)

    @app.route("/")
    def dashboard():
        stats = ReportService().dashboard_stats()
        return render_template("dashboard.html", stats=stats)

    @app.cli.command("init-db")
    def init_db_command():
        """Initialize SQLite database tables."""
        init_db()
        app.logger.info("Database initialized successfully.")
        print("Database initialized successfully.")

    return app


def _ensure_runtime_directories(app):
    """Create folders used for uploaded files, embeddings, database, and logs."""
    for key in ("UPLOAD_FOLDER", "EMBEDDING_FOLDER", "DATABASE_DIR", "LOG_DIR"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)


def _configure_logging(app):
    """Configure file and console logging for development and production."""
    log_file = Path(app.config["LOG_DIR"]) / "app.log"
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
