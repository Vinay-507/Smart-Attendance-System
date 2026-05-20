def cosine_similarity(vector_a, vector_b) -> float:
    """Calculate cosine similarity between two embedding vectors."""
    import numpy as np

    a = np.asarray(vector_a, dtype="float32")
    b = np.asarray(vector_b, dtype="float32")

    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)
