from dataclasses import dataclass


@dataclass
class FaceDetection:
    """Detected face region from RetinaFace."""

    bounding_box: tuple[int, int, int, int]
    confidence: float
    landmarks: dict | None = None


@dataclass
class StudentMatch:
    """Best database match for a detected face."""

    student_id: int | None
    roll_number: str | None
    full_name: str | None
    similarity: float
    is_known: bool


@dataclass
class RecognitionResult:
    """Final recognition result for one face in a classroom image."""

    face_index: int
    bounding_box: tuple[int, int, int, int]
    detection_confidence: float
    student_id: int | None
    roll_number: str | None
    full_name: str | None
    similarity: float
    status: str
