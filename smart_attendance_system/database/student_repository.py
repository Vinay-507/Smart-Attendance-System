from sqlite3 import IntegrityError

from database.db import get_db
from models.student import Student


class StudentRepository:
    """SQLite storage operations for students, face images, and embeddings."""

    def create_student(self, student: Student) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO students (roll_number, full_name, email, class_name, section)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                student.roll_number,
                student.full_name,
                student.email,
                student.class_name,
                student.section,
            ),
        )
        return cursor.lastrowid

    def add_face_image(self, student_id: int, image_path: str) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO student_face_images (student_id, image_path)
            VALUES (?, ?)
            """,
            (student_id, image_path),
        )
        return cursor.lastrowid

    def add_embedding(self, student_id: int, embedding_path: str, model_name: str) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO face_embeddings (student_id, embedding_path, model_name)
            VALUES (?, ?, ?)
            """,
            (student_id, embedding_path, model_name),
        )
        return cursor.lastrowid

    def delete_student(self, student_id: int) -> None:
        db = get_db()
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))

    def list_students(self):
        db = get_db()
        return db.execute(
            """
            SELECT
                s.id,
                s.roll_number,
                s.full_name,
                s.email,
                s.class_name,
                s.section,
                s.created_at,
                COUNT(DISTINCT i.id) AS image_count,
                COUNT(DISTINCT e.id) AS embedding_count
            FROM students s
            LEFT JOIN student_face_images i ON i.student_id = s.id
            LEFT JOIN face_embeddings e ON e.student_id = s.id
            GROUP BY s.id
            ORDER BY s.created_at DESC
            """
        ).fetchall()

    def list_registered_embeddings(self):
        db = get_db()
        return db.execute(
            """
            SELECT
                e.id AS embedding_id,
                e.embedding_path,
                e.model_name,
                s.id AS student_id,
                s.roll_number,
                s.full_name
            FROM face_embeddings e
            JOIN students s ON s.id = e.student_id
            ORDER BY s.id, e.id
            """
        ).fetchall()

    def count_students(self) -> int:
        db = get_db()
        row = db.execute("SELECT COUNT(*) AS total FROM students").fetchone()
        return int(row["total"])

    def rollback(self):
        get_db().rollback()

    def commit(self):
        get_db().commit()


class DuplicateStudentError(ValueError):
    """Raised when roll number or email already exists."""


def is_unique_constraint_error(error: IntegrityError) -> bool:
    message = str(error).lower()
    return "unique constraint failed" in message
