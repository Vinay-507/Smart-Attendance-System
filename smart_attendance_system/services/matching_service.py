from pathlib import Path

from models.recognition import StudentMatch
from recognition_config import RecognitionSettings, load_recognition_settings
from utils.similarity import cosine_similarity


class FaceMatchingService:
    """Match ArcFace embeddings against registered student embeddings."""

    def __init__(self, settings: RecognitionSettings | None = None):
        self.settings = settings or load_recognition_settings()

    def find_best_match(self, face_embedding, registered_embeddings) -> StudentMatch:
        import numpy as np

        best_student = None
        best_similarity = -1.0

        for row in registered_embeddings:
            embedding_path = Path(row["embedding_path"])
            if not embedding_path.exists():
                continue

            stored_embedding = np.load(embedding_path)
            similarity = cosine_similarity(face_embedding, stored_embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_student = row

        is_known = (
            best_student is not None
            and best_similarity >= self.settings.cosine_match_threshold
        )

        if not is_known:
            return StudentMatch(
                student_id=None,
                roll_number=None,
                full_name=None,
                similarity=max(best_similarity, 0.0),
                is_known=False,
            )

        return StudentMatch(
            student_id=best_student["student_id"],
            roll_number=best_student["roll_number"],
            full_name=best_student["full_name"],
            similarity=best_similarity,
            is_known=True,
        )
