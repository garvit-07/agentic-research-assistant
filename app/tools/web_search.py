"""Web search tool. Uses Tavily if TAVILY_API_KEY is set, otherwise DuckDuckGo (no key)."""
import asyncio

from langchain_core.tools import tool

from app.config import settings

MAX_CHARS = 6000


def _format(results: list[dict]) -> str:
    if not results:
        return "No results found."
    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(f"[{i}] {r['title']}\nURL: {r['url']}\n{r['snippet']}")
    return "\n\n".join(blocks)[:MAX_CHARS]


async def _tavily(query: str) -> list[dict]:
    from tavily import AsyncTavilyClient

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    data = await client.search(query=query, max_results=5)
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in data.get("results", [])
    ]


async def _duckduckgo(query: str) -> list[dict]:
    from ddgs import DDGS

    def run() -> list[dict]:
        return DDGS().text(query, max_results=5)

    raw = await asyncio.to_thread(run)
    return [
        {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
        for r in raw
    ]


@tool
async def web_search(query: str) -> str:
    """Search the public web for current or external information.

    Use for recent events, statistics, or anything not in the uploaded documents.
    Returns numbered results with title, URL and a snippet.
    """
    results = await (_tavily(query) if settings.tavily_api_key else _duckduckgo(query))
    return _format(results)
