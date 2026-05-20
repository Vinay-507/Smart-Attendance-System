from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from database.student_repository import DuplicateStudentError
from models.student import Student
from services.embedding_service import EmbeddingGenerationError
from services.student_service import StudentRegistrationError, StudentService
from utils.file_utils import allowed_image_file


students_bp = Blueprint("students", __name__, url_prefix="/students")


@students_bp.route("/", methods=["GET"])
def list_students():
    students = StudentService().list_students()
    return render_template("students/list.html", students=students)


@students_bp.route("/register", methods=["GET", "POST"])
def register_student():
    if request.method == "GET":
        return render_template("students/register.html")

    form_student = Student(
        roll_number=request.form.get("roll_number", "").strip(),
        full_name=request.form.get("full_name", "").strip(),
        email=request.form.get("email", "").strip() or None,
        class_name=request.form.get("class_name", "").strip() or None,
        section=request.form.get("section", "").strip() or None,
    )
    image_files = request.files.getlist("face_images")

    validation_error = _validate_registration_form(form_student, image_files)
    if validation_error:
        flash(validation_error, "danger")
        return render_template("students/register.html", student=form_student), 400

    valid_images = [
        file
        for file in image_files
        if file and file.filename and allowed_image_file(
            file.filename,
            current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
        )
    ]

    try:
        student_id = StudentService().register_student(form_student, valid_images)
        current_app.logger.info("Registered student id=%s", student_id)
        flash("Student registered and face embeddings generated successfully.", "success")
        return redirect(url_for("students.list_students"))

    except (DuplicateStudentError, StudentRegistrationError, EmbeddingGenerationError) as exc:
        current_app.logger.warning("Student registration failed: %s", exc)
        flash(str(exc), "danger")
        return render_template("students/register.html", student=form_student), 400

    except Exception:
        current_app.logger.exception("Unexpected student registration error")
        flash("Registration failed due to an unexpected server error.", "danger")
        return render_template("students/register.html", student=form_student), 500


def _validate_registration_form(student: Student, image_files) -> str | None:
    if not student.roll_number:
        return "Roll number is required."
    if not student.full_name:
        return "Full name is required."
    if not image_files or all(file.filename == "" for file in image_files):
        return "Upload at least one face image."

    allowed_extensions = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    invalid_files = [
        file.filename
        for file in image_files
        if file and file.filename and not allowed_image_file(file.filename, allowed_extensions)
    ]
    if invalid_files:
        return "Only PNG, JPG, JPEG, and WEBP images are allowed."

    return None
