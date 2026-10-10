"""Document retrieval tool over the user's uploaded / ingested knowledge base."""
from langchain_core.tools import tool

from app.config import settings
from app.retrieval.vector_store import get_vector_store


@tool
async def search_documents(query: str) -> str:
    """Search the private knowledge base of uploaded documents (PDF, Markdown, text).

    Use first when the question may relate to the user's own files or notes.
    Returns the most relevant passages with their source file.
    """
    docs = await get_vector_store().asimilarity_search(query, k=settings.retrieval_k)
    if not docs:
        return "No relevant passages found in the uploaded documents."
    blocks = []
    for i, d in enumerate(docs, 1):
        page = f" (page {d.metadata['page']})" if "page" in d.metadata else ""
        blocks.append(f"[{i}] Source: {d.metadata.get('source', 'unknown')}{page}\n{d.page_content}")
    return "\n\n".join(blocks)
