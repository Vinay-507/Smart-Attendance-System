from functools import lru_cache
from pathlib import Path

from models.recognition import FaceDetection
from recognition_config import RecognitionSettings, load_recognition_settings


class FaceDetectionError(RuntimeError):
    """Raised when RetinaFace cannot detect faces from an image."""


class RetinaFaceDetectionService:
    """Detect classroom faces with the pretrained RetinaFace model."""

    def __init__(self, settings: RecognitionSettings | None = None):
        self.settings = settings or load_recognition_settings()

    def detect_faces(self, image_path: Path) -> list[FaceDetection]:
        try:
            import cv2
        except ImportError as exc:
            raise FaceDetectionError(
                "OpenCV is required. Run: pip install -r requirements.txt"
            ) from exc

        image = cv2.imread(str(image_path))
        if image is None:
            raise FaceDetectionError("The classroom image could not be read.")

        raw_faces = _detect_with_retinaface(str(image_path))
        detections: list[FaceDetection] = []

        for face_data in raw_faces.values():
            confidence = float(face_data.get("score", 0.0))
            if confidence < self.settings.retinaface_confidence_threshold:
                continue

            x1, y1, x2, y2 = self._clip_box(face_data["facial_area"], image.shape)
            if self._too_small(x1, y1, x2, y2):
                continue

            detections.append(
                FaceDetection(
                    bounding_box=(x1, y1, x2, y2),
                    confidence=confidence,
                    landmarks=face_data.get("landmarks"),
                )
            )

        return detections

    def _clip_box(self, box, image_shape) -> tuple[int, int, int, int]:
        height, width = image_shape[:2]
        x1, y1, x2, y2 = [int(round(value)) for value in box]
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))
        return x1, y1, x2, y2

    def _too_small(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        return (
            x2 - x1 < self.settings.minimum_face_size
            or y2 - y1 < self.settings.minimum_face_size
        )


@lru_cache(maxsize=1)
def _retinaface_model():
    try:
        from retinaface import RetinaFace
    except ImportError as exc:
        raise FaceDetectionError(
            "RetinaFace is not installed. Run: pip install -r requirements.txt"
        ) from exc
    return RetinaFace


def _detect_with_retinaface(image_path: str) -> dict:
    detector = _retinaface_model()
    faces = detector.detect_faces(image_path)
    if isinstance(faces, dict):
        return faces
    return {}
