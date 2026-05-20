from pathlib import Path
from sqlite3 import IntegrityError

from flask import current_app

from database.student_repository import (
    DuplicateStudentError,
    StudentRepository,
    is_unique_constraint_error,
)
from models.student import Student
from services.embedding_service import ArcFaceEmbeddingService
from utils.file_utils import build_unique_filename


class StudentRegistrationError(ValueError):
    """Raised when student registration cannot be completed."""


class StudentService:
    """Business logic for registering students with face images."""

    def __init__(self):
        self.repository = StudentRepository()
        self.embedding_service = ArcFaceEmbeddingService()

    def register_student(self, student: Student, image_files) -> int:
        if not image_files:
            raise StudentRegistrationError("Upload at least one face image.")

        saved_image_paths: list[Path] = []
        saved_embedding_paths: list[Path] = []
        student_id = None

        try:
            student_id = self.repository.create_student(student)
            self.repository.commit()

            for image_file in image_files:
                if not image_file or image_file.filename == "":
                    continue

                image_path = self._save_student_image(student_id, image_file)
                saved_image_paths.append(image_path)

                embedding = self.embedding_service.generate_embedding(image_path)
                embedding_path = self._embedding_path(student_id, image_path)
                self.embedding_service.save_embedding(embedding, embedding_path)
                saved_embedding_paths.append(embedding_path)

                self.repository.add_face_image(student_id, str(image_path))
                self.repository.add_embedding(
                    student_id,
                    str(embedding_path),
                    self.embedding_service.model_name,
                )

            if not saved_embedding_paths:
                raise StudentRegistrationError("No valid face images were uploaded.")

            self.repository.commit()
            return student_id

        except IntegrityError as exc:
            self.repository.rollback()
            if student_id is not None:
                self._delete_student_record(student_id)
            self._delete_files(saved_image_paths + saved_embedding_paths)
            if is_unique_constraint_error(exc):
                raise DuplicateStudentError(
                    "A student with this roll number or email already exists."
                ) from exc
            raise

        except Exception:
            self.repository.rollback()
            if student_id is not None:
                self._delete_student_record(student_id)
            self._delete_files(saved_image_paths + saved_embedding_paths)
            raise

    def list_students(self):
        return self.repository.list_students()

    def _save_student_image(self, student_id: int, image_file) -> Path:
        upload_root = Path(current_app.config["UPLOAD_FOLDER"])
        student_dir = upload_root / "students" / str(student_id)
        student_dir.mkdir(parents=True, exist_ok=True)

        filename = build_unique_filename(image_file.filename)
        image_path = student_dir / filename
        image_file.save(image_path)
        return image_path

    def _embedding_path(self, student_id: int, image_path: Path) -> Path:
        embedding_root = Path(current_app.config["EMBEDDING_FOLDER"])
        return embedding_root / "students" / str(student_id) / f"{image_path.stem}.npy"

    def _delete_files(self, paths: list[Path]) -> None:
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                current_app.logger.warning("Could not delete file: %s", path)

    def _delete_student_record(self, student_id: int) -> None:
        try:
            self.repository.delete_student(student_id)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            current_app.logger.warning("Could not delete partial student id=%s", student_id)
