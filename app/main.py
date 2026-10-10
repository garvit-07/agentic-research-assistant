import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app import __version__
from app.agent import build_graph
from app.api.routes import chat, documents, health, threads
from app.config import settings
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    # Persistent memory: every graph step is checkpointed to SQLite, keyed by thread_id.
    async with AsyncSqliteSaver.from_conn_string(str(settings.checkpoint_db)) as saver:
        app.state.checkpointer = saver
        app.state.graph = build_graph(saver)
        logger.info("Agent graph ready (model=%s/%s)", settings.llm_provider, settings.llm_model)
        yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="LangGraph research agent: plan -> research (tools) -> write -> self-review.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
for r in (chat.router, threads.router, documents.router):
    app.include_router(r, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
