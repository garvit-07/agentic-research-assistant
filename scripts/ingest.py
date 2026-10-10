"""Index every supported file in a folder (default: data/docs).

Usage:  python -m scripts.ingest [folder]
"""
import asyncio
import sys
from pathlib import Path

from app.config import settings
from app.retrieval.ingest import SUPPORTED_EXTENSIONS, ingest_file


async def main(folder: Path) -> None:
    files = [p for p in sorted(folder.rglob("*")) if p.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not files:
        print(f"No supported files found in {folder}")
        return
    for path in files:
        n = await ingest_file(path)
        print(f"Indexed {path.name}: {n} chunks")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else settings.docs_dir
    asyncio.run(main(target))
