import secrets

from fastapi import Header, HTTPException, Request, status

from app.config import settings


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Optional API-key auth: enforced only when API_KEY is configured."""
    if settings.api_key and not secrets.compare_digest(x_api_key or "", settings.api_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing X-API-Key")


def get_graph(request: Request):
    return request.app.state.graph
