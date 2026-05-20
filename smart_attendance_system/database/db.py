import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    """Return one SQLite connection per request/app context."""
    if "db" not in g:
        database_path = Path(current_app.config["DATABASE_PATH"])
        database_path.parent.mkdir(parents=True, exist_ok=True)

        g.db = sqlite3.connect(database_path, timeout=30)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 30000")
        g.db.execute("PRAGMA journal_mode = WAL")

    return g.db


def close_db(error=None):
    """Close the request/app-context database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create all database tables from schema.sql."""
    db = get_db()
    schema_path = Path(__file__).with_name("schema.sql")

    with schema_path.open("r", encoding="utf-8") as schema_file:
        db.executescript(schema_file.read())

    db.commit()
