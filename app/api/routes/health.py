from fastapi import APIRouter, Request

from app import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/ready")
async def ready(request: Request) -> dict:
    return {"ready": getattr(request.app.state, "graph", None) is not None}
