"""Load PDF / Markdown / text files, chunk them, and index them in Chroma."""
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.retrieval.vector_store import get_vector_store

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}


def load_file(path: Path) -> list[Document]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return [
            Document(page_content=page.extract_text() or "", metadata={"source": path.name, "page": i + 1})
            for i, page in enumerate(reader.pages)
        ]
    if suffix in {".md", ".txt"}:
        return [Document(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name})]
    raise ValueError(f"Unsupported file type: {suffix}")


async def ingest_file(path: Path) -> int:
    """Index a file and return the number of chunks stored."""
    docs = [d for d in load_file(path) if d.page_content.strip()]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    chunks = splitter.split_documents(docs)
    if chunks:
        await get_vector_store().aadd_documents(chunks)
    return len(chunks)
