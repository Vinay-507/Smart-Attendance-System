from datetime import datetime
from pathlib import Path

from flask import current_app

from database.attendance_repository import AttendanceRepository
from database.student_repository import StudentRepository
from models.attendance import AttendanceDraftRow
from services.recognition_pipeline import FaceRecognitionPipeline
from utils.file_utils import build_unique_filename


class AttendanceError(ValueError):
    """Raised when attendance generation or saving fails."""


class AttendanceService:
    """Generate, correct, and save attendance from a classroom image."""

    def __init__(self):
        self.attendance_repository = AttendanceRepository()
        self.student_repository = StudentRepository()
        self.recognition_pipeline = FaceRecognitionPipeline()

    def generate_draft(self, image_file) -> dict:
        if not image_file or image_file.filename == "":
            raise AttendanceError("Upload a classroom image.")

        image_path = self._save_classroom_image(image_file)
        recognition_results = self.recognition_pipeline.recognize_classroom_image(image_path)
        students = self.student_repository.list_students()
        recognized_map = self._best_recognition_per_student(recognition_results)

        now = datetime.now()
        session_id = self.attendance_repository.create_session(
            classroom_image_path=str(image_path),
            session_date=now.date().isoformat(),
            session_time=now.time().replace(microsecond=0).isoformat(),
            total_faces_detected=len(recognition_results),
        )
        self.attendance_repository.commit()

        draft_rows = [
            AttendanceDraftRow(
                student_id=student["id"],
                roll_number=student["roll_number"],
                full_name=student["full_name"],
                class_name=student["class_name"],
                section=student["section"],
                predicted_present=student["id"] in recognized_map,
                confidence=recognized_map.get(student["id"]),
            )
            for student in students
        ]

        unknown_faces = [
            result for result in recognition_results if result.status != "recognized"
        ]

        return {
            "session_id": session_id,
            "session_date": now.date().isoformat(),
            "session_time": now.time().replace(microsecond=0).isoformat(),
            "image_path": image_path,
            "draft_rows": draft_rows,
            "recognition_results": recognition_results,
            "unknown_faces": unknown_faces,
        }

    def save_corrected_attendance(
        self,
        session_id: int,
        present_student_ids: set[int],
        predicted_present_ids: set[int],
        confidence_by_student: dict[int, float],
    ) -> None:
        session = self.attendance_repository.get_session(session_id)
        if session is None:
            raise AttendanceError("Attendance session was not found.")

        students = self.student_repository.list_students()
        records = []

        for student in students:
            student_id = student["id"]
            final_present = student_id in present_student_ids
            predicted_present = student_id in predicted_present_ids
            manually_corrected = int(final_present != predicted_present)

            records.append(
                {
                    "student_id": student_id,
                    "attendance_date": session["session_date"],
                    "attendance_time": session["session_time"],
                    "status": "present" if final_present else "absent",
                    "confidence": confidence_by_student.get(student_id),
                    "manually_corrected": manually_corrected,
                }
            )

        try:
            self.attendance_repository.replace_records(session_id, records)
            self.attendance_repository.commit()
        except Exception:
            self.attendance_repository.rollback()
            raise

    def list_saved_records(self, session_id: int):
        session = self.attendance_repository.get_session(session_id)
        if session is None:
            raise AttendanceError("Attendance session was not found.")
        records = self.attendance_repository.list_records_for_session(session_id)
        return session, records

    def _save_classroom_image(self, image_file) -> Path:
        upload_root = Path(current_app.config["UPLOAD_FOLDER"])
        classroom_dir = upload_root / "classroom"
        classroom_dir.mkdir(parents=True, exist_ok=True)

        filename = build_unique_filename(image_file.filename)
        image_path = classroom_dir / filename
        image_file.save(image_path)
        return image_path

    def _best_recognition_per_student(self, recognition_results) -> dict[int, float]:
        recognized_map: dict[int, float] = {}

        for result in recognition_results:
            if result.status != "recognized" or result.student_id is None:
                continue

            current_confidence = recognized_map.get(result.student_id, -1.0)
            if result.similarity > current_confidence:
                recognized_map[result.student_id] = result.similarity

        return recognized_map
