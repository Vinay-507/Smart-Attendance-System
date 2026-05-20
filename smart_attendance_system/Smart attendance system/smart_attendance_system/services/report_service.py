from database.attendance_repository import AttendanceRepository
from database.student_repository import StudentRepository


class ReportService:
    """Prepare attendance report data for HTML pages and JSON APIs."""

    def __init__(self):
        self.attendance_repository = AttendanceRepository()
        self.student_repository = StudentRepository()

    def report(self, attendance_date: str | None = None, student_id: int | None = None):
        records = self.attendance_repository.list_records(attendance_date, student_id)
        summary = self.attendance_repository.summary(attendance_date, student_id)
        students = self.student_repository.list_students()
        return {
            "records": records,
            "summary": summary,
            "students": students,
            "selected_date": attendance_date or "",
            "selected_student_id": student_id,
        }

    def dashboard_stats(self):
        total_students = self.student_repository.count_students()
        total_sessions = self.attendance_repository.count_sessions()
        present_records = self.attendance_repository.count_records_by_status("present")
        absent_records = self.attendance_repository.count_records_by_status("absent")
        total_records = present_records + absent_records
        attendance_percentage = (
            round((present_records / total_records) * 100, 2) if total_records else 0.0
        )

        return {
            "total_students": total_students,
            "total_sessions": total_sessions,
            "present_records": present_records,
            "absent_records": absent_records,
            "attendance_percentage": attendance_percentage,
        }
