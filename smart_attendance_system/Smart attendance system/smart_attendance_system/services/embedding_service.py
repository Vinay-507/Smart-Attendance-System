from functools import lru_cache
from pathlib import Path


class EmbeddingGenerationError(RuntimeError):
    """Raised when a face embedding cannot be generated from an image."""


class ArcFaceEmbeddingService:
    """Generate ArcFace embeddings using InsightFace pretrained models."""

    model_name = "insightface-buffalo_l-arcface"

    def generate_embedding(self, image_path: Path):
        """
        Detect faces and return one normalized ArcFace embedding.

        Registration images should contain one student. If multiple faces are
        found, the largest detected face is used because it is normally the
        intended foreground face in a registration photo.
        """
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise EmbeddingGenerationError(
                "OpenCV and NumPy are required. Run: pip install -r requirements.txt"
            ) from exc

        image = cv2.imread(str(image_path))
        if image is None:
            raise EmbeddingGenerationError("The uploaded image could not be read.")

        face_app = _get_face_analysis_app()
        faces = face_app.get(image)

        if not faces:
            raise EmbeddingGenerationError(
                "No face was detected. Upload a clear front-facing student image."
            )

        selected_face = max(faces, key=_face_area)
        embedding = np.asarray(selected_face.embedding, dtype=np.float32)

        norm = np.linalg.norm(embedding)
        if norm == 0:
            raise EmbeddingGenerationError("The face embedding is empty.")

        return embedding / norm

    def save_embedding(self, embedding, output_path: Path) -> None:
        import numpy as np

        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(output_path, embedding)


def _face_area(face) -> float:
    x1, y1, x2, y2 = face.bbox
    return max(0.0, float(x2 - x1)) * max(0.0, float(y2 - y1))


@lru_cache(maxsize=1)
def _get_face_analysis_app():
    """
    Lazily load InsightFace so app startup remains fast.

    The first registration request may download pretrained weights into the
    user's InsightFace model cache if they are not already present.
    """
    try:
        from insightface.app import FaceAnalysis
    except ImportError as exc:
        raise EmbeddingGenerationError(
            "InsightFace is not installed. Run: pip install -r requirements.txt"
        ) from exc

    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    return app
