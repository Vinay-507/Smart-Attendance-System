import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RecognitionSettings:
    """Thresholds and model settings for face recognition."""

    cosine_match_threshold: float = 0.45
    retinaface_confidence_threshold: float = 0.90
    minimum_face_size: int = 32
    arcface_model_name: str = "buffalo_l"
    arcface_providers: tuple[str, ...] = ("CPUExecutionProvider",)


def load_recognition_settings() -> RecognitionSettings:
    """Load recognition settings separately from the general Flask config."""
    providers = os.getenv("ARCFACE_PROVIDERS", "CPUExecutionProvider")
    return RecognitionSettings(
        cosine_match_threshold=float(os.getenv("COSINE_MATCH_THRESHOLD", "0.45")),
        retinaface_confidence_threshold=float(
            os.getenv("RETINAFACE_CONFIDENCE_THRESHOLD", "0.90")
        ),
        minimum_face_size=int(os.getenv("MINIMUM_FACE_SIZE", "32")),
        arcface_model_name=os.getenv("ARCFACE_MODEL_NAME", "buffalo_l"),
        arcface_providers=tuple(item.strip() for item in providers.split(",") if item.strip()),
    )
