from functools import lru_cache

from recognition_config import RecognitionSettings, load_recognition_settings


class ArcFaceRecognitionError(RuntimeError):
    """Raised when ArcFace cannot generate a usable face embedding."""


class ArcFaceRecognitionService:
    """Generate ArcFace embeddings for detected face crops."""

    def __init__(self, settings: RecognitionSettings | None = None):
        self.settings = settings or load_recognition_settings()

    def embedding_from_crop(self, image, bounding_box: tuple[int, int, int, int]):
        """
        Crop a RetinaFace detection and generate a normalized ArcFace embedding.

        The crop is expanded slightly so InsightFace can locate facial landmarks
        inside the cropped region before running ArcFace.
        """
        import numpy as np

        crop = self._crop_with_margin(image, bounding_box)
        if crop.size == 0:
            raise ArcFaceRecognitionError("Detected face crop is empty.")

        face_app = _get_arcface_app(
            self.settings.arcface_model_name,
            self.settings.arcface_providers,
        )
        faces = face_app.get(crop)

        if not faces:
            raise ArcFaceRecognitionError("ArcFace could not extract this face embedding.")

        selected_face = max(faces, key=_face_area)
        embedding = np.asarray(selected_face.embedding, dtype="float32")
        norm = np.linalg.norm(embedding)
        if norm == 0:
            raise ArcFaceRecognitionError("ArcFace generated an empty embedding.")

        return embedding / norm

    def _crop_with_margin(self, image, box: tuple[int, int, int, int], margin_ratio=0.18):
        height, width = image.shape[:2]
        x1, y1, x2, y2 = box
        face_width = x2 - x1
        face_height = y2 - y1
        margin_x = int(face_width * margin_ratio)
        margin_y = int(face_height * margin_ratio)

        crop_x1 = max(0, x1 - margin_x)
        crop_y1 = max(0, y1 - margin_y)
        crop_x2 = min(width, x2 + margin_x)
        crop_y2 = min(height, y2 + margin_y)
        return image[crop_y1:crop_y2, crop_x1:crop_x2]


def _face_area(face) -> float:
    x1, y1, x2, y2 = face.bbox
    return max(0.0, float(x2 - x1)) * max(0.0, float(y2 - y1))


@lru_cache(maxsize=4)
def _get_arcface_app(model_name: str, providers: tuple[str, ...]):
    try:
        from insightface.app import FaceAnalysis
    except ImportError as exc:
        raise ArcFaceRecognitionError(
            "InsightFace is not installed. Run: pip install -r requirements.txt"
        ) from exc

    app = FaceAnalysis(name=model_name, providers=list(providers))
    app.prepare(ctx_id=-1, det_size=(320, 320))
    return app
