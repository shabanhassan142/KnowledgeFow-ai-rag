from fastapi import APIRouter, Depends, UploadFile, File, Query, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from loguru import logger

from app.db.session import get_db, SessionLocal
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService
from app.storage.local_storage import local_storage

router = APIRouter(prefix="/documents", tags=["Documents"])


def _process_document_sync_fallback(doc_id: str):
    """Fallback runner if Celery/Redis is unavailable."""
    from app.models.document import DocumentStatus, ProcessingStage, Document
    from app.rag.pipeline import DocumentPipeline
    db = SessionLocal()
    try:
        service = DocumentService(db)
        service.update_status(doc_id, DocumentStatus.processing)
        doc = db.query(Document).filter_by(id=doc_id).first()
        if doc:
            doc.processing_stage = ProcessingStage.queued
            db.commit()
        pipeline = DocumentPipeline(db)
        chunk_count = pipeline.process(doc_id)
        service.update_status(doc_id, DocumentStatus.ready)
        logger.info(f"[FallbackTask] Done: {doc_id} — {chunk_count} chunks")
    except Exception as exc:
        logger.error(f"[FallbackTask] Failed: {doc_id} — {exc}")
        service = DocumentService(db)
        service.update_status(doc_id, DocumentStatus.failed, error=str(exc))
    finally:
        db.close()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Upload one or multiple documents. Admin only."""
    service = DocumentService(db)
    docs = service.upload_documents(files, current_user)

    # Trigger background processing (Celery with BackgroundTasks fallback)
    from app.workers.document_tasks import process_document_task
    for doc in docs:
        try:
            process_document_task.delay(str(doc.id))
        except Exception as exc:
            logger.warning(f"[Upload] Celery unavailable ({exc}), queuing via BackgroundTasks")
            background_tasks.add_task(_process_document_sync_fallback, str(doc.id))

    return DocumentUploadResponse(
        message=f"{len(docs)} document(s) uploaded and queued for processing",
        documents=[DocumentResponse.model_validate(d) for d in docs],
    )


@router.get("", response_model=DocumentListResponse)
@router.get("/", response_model=DocumentListResponse, include_in_schema=False)
def list_documents(
    file_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents with optional filters. All authenticated users."""
    service = DocumentService(db)
    total, items = service.list_documents(
        file_type=file_type,
        status_filter=status,
        search=search,
        skip=skip,
        limit=limit,
    )
    return DocumentListResponse(
        total=total,
        items=[DocumentResponse.model_validate(d) for d in items],
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document details by ID."""
    service = DocumentService(db)
    return DocumentResponse.model_validate(service.get_document(doc_id))


@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll document processing status."""
    service = DocumentService(db)
    doc = service.get_document(doc_id)
    return DocumentStatusResponse.model_validate(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a document and its chunks. Admin only."""
    service = DocumentService(db)
    service.delete_document(doc_id)


@router.put("/{doc_id}/replace", response_model=DocumentResponse)
def replace_document(
    doc_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Replace an existing document with a new file. Admin only."""
    service = DocumentService(db)
    doc = service.replace_document(doc_id, file, current_user)

    # Re-queue for processing
    from app.workers.document_tasks import process_document_task
    try:
        process_document_task.delay(str(doc.id))
    except Exception as exc:
        logger.warning(f"[Replace] Celery unavailable ({exc}), queuing via BackgroundTasks")
        background_tasks.add_task(_process_document_sync_fallback, str(doc.id))

    return DocumentResponse.model_validate(doc)


@router.get("/{doc_id}/download")
def download_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the original uploaded file."""
    service = DocumentService(db)
    doc = service.get_document(doc_id)

    if not local_storage.exists(doc.file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type="application/octet-stream",
    )
