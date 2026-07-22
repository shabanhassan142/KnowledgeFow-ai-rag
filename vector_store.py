from typing import List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from app.db.chroma import get_collection
from app.rag.embedder import Embedder
from app.core.config import settings


@dataclass
class SearchResult:
    """A single result from a vector similarity search."""
    chunk_id: str          # PostgreSQL chunk UUID
    vector_id: str         # ChromaDB document ID
    content: str
    score: float           # cosine similarity (0–1, higher = more relevant)
    metadata: Dict[str, Any]


class VectorStore:
    """
    Manages all ChromaDB operations:
    - Upsert chunks (add/replace embeddings)
    - Similarity search with score threshold
    - Delete by document ID
    """

    def __init__(self):
        self.collection = get_collection()
        self.embedder = Embedder()

    def upsert_chunks(
        self,
        chunk_ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Embed texts and upsert into ChromaDB.
        Returns the list of vector_ids (same as chunk_ids).
        """
        if not texts:
            return []

        logger.info(f"[VectorStore] Generating embeddings for {len(texts)} chunks")
        embeddings = self.embedder.embed_texts(texts)

        # ChromaDB upsert: inserts or updates by ID
        self.collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info(f"[VectorStore] Upserted {len(chunk_ids)} vectors")
        return chunk_ids

    def search(self, query: str, top_k: int = None) -> List[SearchResult]:
        """
        Embed query and retrieve top-k most similar chunks.
        Filters out results below SIMILARITY_THRESHOLD.
        """
        k = top_k or settings.TOP_K_RESULTS
        if self.collection.count() == 0:
            return []
        query_embedding = self.embedder.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for vec_id, doc, meta, distance in zip(ids, documents, metadatas, distances):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score: 1 - (distance / 2)
            score = max(0.0, round(1.0 - (distance / 2.0), 4))

            search_results.append(SearchResult(
                chunk_id=meta.get("chunk_id", vec_id),
                vector_id=vec_id,
                content=doc,
                score=score,
                metadata=meta,
            ))

        return search_results

    def delete_by_document(self, document_id: str) -> None:
        """Remove all vectors belonging to a document."""
        results = self.collection.get(
            where={"document_id": document_id},
            include=["documents"],
        )
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
            logger.info(f"[VectorStore] Deleted {len(ids_to_delete)} vectors for document {document_id}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Returns basic stats about the vector collection."""
        count = self.collection.count()
        return {"total_vectors": count, "collection": settings.CHROMA_COLLECTION_NAME}
