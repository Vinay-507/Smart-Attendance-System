from flask import Blueprint, jsonify, request

from services.report_service import ReportService


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/students", methods=["GET"])
def students_api():
    students = ReportService().student_repository.list_students()
    return jsonify([_student_to_dict(student) for student in students])


@api_bp.route("/attendance", methods=["GET"])
def attendance_api():
    attendance_date = request.args.get("date", "").strip() or None
    student_id_raw = request.args.get("student_id", "").strip()
    student_id = int(student_id_raw) if student_id_raw.isdigit() else None

    report = ReportService().report(attendance_date, student_id)
    return jsonify(
        {
            "summary": report["summary"],
            "records": [_record_to_dict(record) for record in report["records"]],
        }
    )


def _student_to_dict(student):
    return {
        "id": student["id"],
        "roll_number": student["roll_number"],
        "full_name": student["full_name"],
        "email": student["email"],
        "class_name": student["class_name"],
        "section": student["section"],
        "image_count": student["image_count"],
        "embedding_count": student["embedding_count"],
        "created_at": student["created_at"],
    }


def _record_to_dict(record):
    return {
        "id": record["id"],
        "session_id": record["session_id"],
        "student_id": record["student_id"],
        "roll_number": record["roll_number"],
        "full_name": record["full_name"],
        "class_name": record["class_name"],
        "section": record["section"],
        "status": record["status"],
        "confidence": record["confidence"],
        "manually_corrected": bool(record["manually_corrected"]),
        "attendance_date": record["attendance_date"],
        "attendance_time": record["attendance_time"],
    }
