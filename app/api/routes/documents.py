import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps import verify_api_key
from app.config import settings
from app.retrieval.ingest import SUPPORTED_EXTENSIONS, ingest_file
from app.schemas import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[Depends(verify_api_key)])


@router.post("", response_model=UploadResponse, summary="Upload and index a document")
async def upload_document(file: UploadFile) -> UploadResponse:
    name = Path(file.filename or "").name  # strip any path components
    if Path(name).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(415, f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB")

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    path = settings.upload_dir / name
    path.write_bytes(content)
    try:
        chunks = await ingest_file(path)
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(422, f"Could not process file: {exc}") from exc
    return UploadResponse(filename=name, chunks=chunks)


@router.get("", summary="List uploaded documents")
async def list_documents() -> dict:
    files = sorted(p.name for p in settings.upload_dir.glob("*")) if settings.upload_dir.exists() else []
    return {"documents": files}
