from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from services.attendance_service import AttendanceError, AttendanceService
from utils.file_utils import allowed_image_file


attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("/capture", methods=["GET", "POST"])
def capture_attendance():
    if request.method == "GET":
        return render_template("attendance/capture.html")

    image_file = request.files.get("classroom_image")
    validation_error = _validate_classroom_image(image_file)
    if validation_error:
        flash(validation_error, "danger")
        return render_template("attendance/capture.html"), 400

    try:
        draft = AttendanceService().generate_draft(image_file)
        return render_template("attendance/correction.html", **draft)
    except AttendanceError as exc:
        current_app.logger.warning("Attendance generation failed: %s", exc)
        flash(str(exc), "danger")
        return render_template("attendance/capture.html"), 400
    except Exception:
        current_app.logger.exception("Unexpected attendance generation error")
        flash("Attendance generation failed due to an unexpected server error.", "danger")
        return render_template("attendance/capture.html"), 500


@attendance_bp.route("/save", methods=["POST"])
def save_attendance():
    try:
        session_id = int(request.form["session_id"])
        present_student_ids = _parse_student_id_set(request.form.getlist("present_student_ids"))
        predicted_present_ids = _parse_student_id_set(
            request.form.getlist("predicted_present_ids")
        )
        confidence_by_student = _parse_confidence_map(request.form)

        AttendanceService().save_corrected_attendance(
            session_id=session_id,
            present_student_ids=present_student_ids,
            predicted_present_ids=predicted_present_ids,
            confidence_by_student=confidence_by_student,
        )

        flash("Attendance saved successfully.", "success")
        return redirect(url_for("attendance.view_session", session_id=session_id))

    except (KeyError, ValueError, AttendanceError) as exc:
        current_app.logger.warning("Attendance save failed: %s", exc)
        flash("Attendance could not be saved. Please regenerate the draft.", "danger")
        return redirect(url_for("attendance.capture_attendance"))

    except Exception:
        current_app.logger.exception("Unexpected attendance save error")
        flash("Attendance save failed due to an unexpected server error.", "danger")
        return redirect(url_for("attendance.capture_attendance"))


@attendance_bp.route("/sessions/<int:session_id>", methods=["GET"])
def view_session(session_id: int):
    try:
        session, records = AttendanceService().list_saved_records(session_id)
        return render_template(
            "attendance/session.html",
            session=session,
            records=records,
        )
    except AttendanceError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("attendance.capture_attendance"))


def _validate_classroom_image(image_file) -> str | None:
    if not image_file or image_file.filename == "":
        return "Upload a classroom image."

    if not allowed_image_file(
        image_file.filename,
        current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
    ):
        return "Only PNG, JPG, JPEG, and WEBP images are allowed."

    return None


def _parse_student_id_set(values: list[str]) -> set[int]:
    return {int(value) for value in values if value.strip()}


def _parse_confidence_map(form_data) -> dict[int, float]:
    confidence_by_student: dict[int, float] = {}

    for key, value in form_data.items():
        if not key.startswith("confidence_") or value == "":
            continue

        student_id = int(key.replace("confidence_", "", 1))
        confidence_by_student[student_id] = float(value)

    return confidence_by_student
