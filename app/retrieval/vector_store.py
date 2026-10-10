"""Chroma vector store (persistent) + embeddings factory."""
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.config import settings


def get_embeddings() -> Embeddings:
    if settings.embedding_provider == "fake":  # offline / tests only
        from langchain_core.embeddings import DeterministicFakeEmbedding

        return DeterministicFakeEmbedding(size=256)
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(model=settings.embedding_model)


@lru_cache
def get_vector_store() -> Chroma:
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name="research_docs",
        embedding_function=get_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )
