from app.tools.document_search import search_documents
from app.tools.web_search import web_search

TOOLS = [web_search, search_documents]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

__all__ = ["TOOLS", "TOOLS_BY_NAME", "web_search", "search_documents"]
