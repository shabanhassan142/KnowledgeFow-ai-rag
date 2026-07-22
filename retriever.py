from typing import List, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from app.rag.vector_store import VectorStore, SearchResult
from app.models.chunk import DocumentChunk
from app.core.config import settings


class RAGRetriever:
    """
    Retrieves relevant chunks for a query.
    Enriches vector search results with full chunk content from PostgreSQL.
    """

    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStore()

    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        1. Embed query and search ChromaDB
        2. Fetch full chunk records from PostgreSQL by chunk_id
        3. Return enriched results sorted by relevance score
        """
        k = top_k or settings.TOP_K_RESULTS
        search_results: List[SearchResult] = self.vector_store.search(query, top_k=k)

        if not search_results:
            logger.info(f"[Retriever] No results above threshold for query: {query[:60]}")
            return []

        # Fetch full chunk details from PostgreSQL (cast string IDs to UUID)
        from uuid import UUID
        valid_uuids = []
        for r in search_results:
            try:
                valid_uuids.append(UUID(str(r.chunk_id)))
            except Exception:
                pass

        db_chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.id.in_(valid_uuids))
            .all()
        )
        chunk_map = {str(c.id): c for c in db_chunks}

        enriched = []
        for result in search_results:
            db_chunk = chunk_map.get(str(result.chunk_id))
            doc_id = str(db_chunk.document_id) if db_chunk else str(result.metadata.get("document_id", ""))
            page_num = db_chunk.page_number if db_chunk else result.metadata.get("page_number", 1)
            heading = (db_chunk.section_heading if db_chunk else "") or result.metadata.get("section_heading", "")
            chunk_idx = db_chunk.chunk_index if db_chunk else result.metadata.get("chunk_index", 0)

            enriched.append({
                "chunk_id": str(result.chunk_id),
                "content": result.content,
                "score": result.score,
                "metadata": {
                    "document_id": doc_id,
                    "document_name": result.metadata.get("document_name", "Document"),
                    "page_number": page_num,
                    "section_heading": heading,
                    "file_type": result.metadata.get("file_type", ""),
                    "chunk_index": chunk_idx,
                },
            })

        logger.info(f"[Retriever] Retrieved {len(enriched)} chunks for query: '{query[:40]}'")
        return enriched
