from database.db import get_db


class AttendanceRepository:
    """SQLite storage operations for attendance sessions and records."""

    def create_session(
        self,
        classroom_image_path: str,
        session_date: str,
        session_time: str,
        total_faces_detected: int,
    ) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO attendance_sessions (
                classroom_image_path,
                session_date,
                session_time,
                total_faces_detected
            )
            VALUES (?, ?, ?, ?)
            """,
            (classroom_image_path, session_date, session_time, total_faces_detected),
        )
        return cursor.lastrowid

    def get_session(self, session_id: int):
        db = get_db()
        return db.execute(
            """
            SELECT id, classroom_image_path, session_date, session_time, total_faces_detected
            FROM attendance_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

    def replace_records(self, session_id: int, records: list[dict]) -> None:
        db = get_db()
        db.execute("DELETE FROM attendance_records WHERE session_id = ?", (session_id,))
        db.executemany(
            """
            INSERT INTO attendance_records (
                session_id,
                student_id,
                attendance_date,
                attendance_time,
                status,
                confidence,
                manually_corrected
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    session_id,
                    record["student_id"],
                    record["attendance_date"],
                    record["attendance_time"],
                    record["status"],
                    record["confidence"],
                    record["manually_corrected"],
                )
                for record in records
            ],
        )

    def list_records_for_session(self, session_id: int):
        db = get_db()
        return db.execute(
            """
            SELECT
                r.id,
                r.status,
                r.confidence,
                r.manually_corrected,
                r.attendance_date,
                r.attendance_time,
                s.roll_number,
                s.full_name,
                s.class_name,
                s.section
            FROM attendance_records r
            JOIN students s ON s.id = r.student_id
            WHERE r.session_id = ?
            ORDER BY s.roll_number
            """,
            (session_id,),
        ).fetchall()

    def list_records(self, attendance_date: str | None = None, student_id: int | None = None):
        db = get_db()
        query = """
            SELECT
                r.id,
                r.session_id,
                r.student_id,
                r.status,
                r.confidence,
                r.manually_corrected,
                r.attendance_date,
                r.attendance_time,
                s.roll_number,
                s.full_name,
                s.class_name,
                s.section
            FROM attendance_records r
            JOIN students s ON s.id = r.student_id
            WHERE 1 = 1
        """
        params: list = []

        if attendance_date:
            query += " AND r.attendance_date = ?"
            params.append(attendance_date)

        if student_id:
            query += " AND r.student_id = ?"
            params.append(student_id)

        query += " ORDER BY r.attendance_date DESC, r.attendance_time DESC, s.roll_number"
        return db.execute(query, params).fetchall()

    def summary(self, attendance_date: str | None = None, student_id: int | None = None):
        db = get_db()
        query = """
            SELECT
                COUNT(*) AS total_records,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS present_count,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) AS absent_count,
                SUM(CASE WHEN manually_corrected = 1 THEN 1 ELSE 0 END) AS corrected_count
            FROM attendance_records
            WHERE 1 = 1
        """
        params: list = []

        if attendance_date:
            query += " AND attendance_date = ?"
            params.append(attendance_date)

        if student_id:
            query += " AND student_id = ?"
            params.append(student_id)

        row = db.execute(query, params).fetchone()
        total = int(row["total_records"] or 0)
        present = int(row["present_count"] or 0)
        absent = int(row["absent_count"] or 0)
        corrected = int(row["corrected_count"] or 0)
        percentage = round((present / total) * 100, 2) if total else 0.0

        return {
            "total_records": total,
            "present_count": present,
            "absent_count": absent,
            "corrected_count": corrected,
            "attendance_percentage": percentage,
        }

    def count_sessions(self) -> int:
        db = get_db()
        row = db.execute("SELECT COUNT(*) AS total FROM attendance_sessions").fetchone()
        return int(row["total"])

    def count_records_by_status(self, status: str) -> int:
        db = get_db()
        row = db.execute(
            "SELECT COUNT(*) AS total FROM attendance_records WHERE status = ?",
            (status,),
        ).fetchone()
        return int(row["total"])

    def commit(self):
        get_db().commit()

    def rollback(self):
        get_db().rollback()
