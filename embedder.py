import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from typing import List, Optional
from loguru import logger
from app.core.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"[Embedder] Loading local model: {settings.EMBEDDING_MODEL}")
        try:
            _model = SentenceTransformer(settings.EMBEDDING_MODEL, local_files_only=True)
        except Exception as e:
            logger.warning(f"[Embedder] Could not load offline ({e}), attempting online fetch...")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("[Embedder] Model loaded")
    return _model


class Embedder:
    """
    Generates embeddings using a local sentence-transformers model.
    No API calls, no quota limits, runs entirely on-device.
    Default model: all-MiniLM-L6-v2 (384 dims, fast, good quality)
    """

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts. Returns list of embedding vectors."""
        if not texts:
            return []
        model = _get_model()
        logger.info(f"[Embedder] Embedding {len(texts)} text(s)")
        embeddings = model.encode(texts, convert_to_numpy=True)
        return [e.tolist() for e in embeddings]

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string for similarity search."""
        return self.embed_texts([query])[0]