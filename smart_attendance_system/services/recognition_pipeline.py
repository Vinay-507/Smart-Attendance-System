from pathlib import Path

from database.student_repository import StudentRepository
from models.recognition import RecognitionResult
from recognition_config import RecognitionSettings, load_recognition_settings
from services.arcface_service import ArcFaceRecognitionError, ArcFaceRecognitionService
from services.face_detection_service import RetinaFaceDetectionService
from services.matching_service import FaceMatchingService


class FaceRecognitionPipeline:
    """RetinaFace detection plus ArcFace recognition for a classroom image."""

    def __init__(self, settings: RecognitionSettings | None = None):
        self.settings = settings or load_recognition_settings()
        self.detector = RetinaFaceDetectionService(self.settings)
        self.arcface = ArcFaceRecognitionService(self.settings)
        self.matcher = FaceMatchingService(self.settings)
        self.student_repository = StudentRepository()

    def recognize_classroom_image(self, image_path: Path) -> list[RecognitionResult]:
        """
        Recognize all detectable students in one classroom image.

        Returns one result per RetinaFace detection. A result is marked unknown
        when the best cosine similarity is below the configured threshold.
        """
        import cv2

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError("The classroom image could not be read.")

        detections = self.detector.detect_faces(image_path)
        registered_embeddings = self.student_repository.list_registered_embeddings()
        results: list[RecognitionResult] = []

        for face_index, detection in enumerate(detections, start=1):
            try:
                face_embedding = self.arcface.embedding_from_crop(
                    image,
                    detection.bounding_box,
                )
                match = self.matcher.find_best_match(
                    face_embedding,
                    registered_embeddings,
                )
                status = "recognized" if match.is_known else "unknown"

                results.append(
                    RecognitionResult(
                        face_index=face_index,
                        bounding_box=detection.bounding_box,
                        detection_confidence=detection.confidence,
                        student_id=match.student_id,
                        roll_number=match.roll_number,
                        full_name=match.full_name,
                        similarity=match.similarity,
                        status=status,
                    )
                )

            except ArcFaceRecognitionError:
                results.append(
                    RecognitionResult(
                        face_index=face_index,
                        bounding_box=detection.bounding_box,
                        detection_confidence=detection.confidence,
                        student_id=None,
                        roll_number=None,
                        full_name=None,
                        similarity=0.0,
                        status="embedding_failed",
                    )
                )

        return results
