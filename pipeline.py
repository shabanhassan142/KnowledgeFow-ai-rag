from sqlalchemy.orm import Session
from loguru import logger

from app.rag.extractors import get_extractor
from app.rag.cleaner import TextCleaner
from app.rag.chunker import DocumentChunker
from app.rag.vector_store import VectorStore
from app.models.document import Document, DocumentStatus, ProcessingStage
from app.models.chunk import DocumentChunk


class DocumentPipeline:
    """
    Orchestrates the full document processing pipeline with granular stage tracking:
    uploaded → queued → extracting → chunking → embedding → saving → completed
    """

    def __init__(self, db: Session):
        self.db = db
        self.cleaner = TextCleaner()
        self.chunker = DocumentChunker()
        self.vector_store = VectorStore()

    def _set_stage(self, doc: Document, stage: ProcessingStage) -> None:
        """Update processing stage and flush immediately so frontend can poll it."""
        doc.processing_stage = stage
        self.db.flush()
        self.db.commit()
        logger.info(f"[Pipeline] Stage: {stage.value} — '{doc.original_filename}'")

    def process(self, document_id: str) -> int:
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Stage: extracting
        self._set_stage(doc, ProcessingStage.extracting)
        extractor = get_extractor(doc.file_type.value)
        pages = extractor.extract(doc.file_path)
        logger.info(f"[Pipeline] Extracted {len(pages)} page(s)")

        # Store total pages
        doc.total_pages = len(pages)
        self.db.commit()

        # Clean pages
        for page in pages:
            page.content = self.cleaner.clean(page.content)

        # Stage: chunking
        self._set_stage(doc, ProcessingStage.chunking)
        chunks = self.chunker.chunk_pages(pages)
        logger.info(f"[Pipeline] Created {len(chunks)} chunk(s)")

        if not chunks:
            raise ValueError("No text content could be extracted from this document")

        # Remove old data
        self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        self.vector_store.delete_by_document(document_id)

        # Persist chunks to PostgreSQL
        db_chunks = []
        for chunk in chunks:
            db_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                token_count=chunk.token_count,
                page_number=chunk.page_number,
                section_heading=chunk.section_heading or None,
                chunk_metadata={
                    "source_filename": doc.original_filename,
                    "file_type": doc.file_type.value,
                    "upload_date": doc.created_at.isoformat(),
                    "uploaded_by": str(doc.uploaded_by),
                    **chunk.metadata,
                },
            )
            self.db.add(db_chunk)
            db_chunks.append(db_chunk)

        self.db.flush()

        # Stage: embedding
        self._set_stage(doc, ProcessingStage.embedding)
        chunk_ids = [str(c.id) for c in db_chunks]
        texts = [c.content for c in db_chunks]
        metadatas = [
            {
                "chunk_id": str(c.id),
                "document_id": str(doc.id),
                "document_name": doc.original_filename,
                "file_type": doc.file_type.value,
                "page_number": c.page_number or 0,
                "section_heading": c.section_heading or "",
                "chunk_index": c.chunk_index,
            }
            for c in db_chunks
        ]
        self.vector_store.upsert_chunks(chunk_ids, texts, metadatas)

        # Stage: saving
        self._set_stage(doc, ProcessingStage.saving)
        for db_chunk, vector_id in zip(db_chunks, chunk_ids):
            db_chunk.vector_id = vector_id

        # Stage: completed
        doc.processing_stage = ProcessingStage.completed
        self.db.commit()
        logger.info(f"[Pipeline] Completed: {len(db_chunks)} chunks for document {document_id}")
        return len(db_chunks)
