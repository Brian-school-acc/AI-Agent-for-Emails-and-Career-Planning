"""Custom tools for the agents. Each function is decorated with @tool
so the framework exposes it. Import these into server.py and attach via tools=[...]."""

from agent_framework import tool          # ⚠️ verify this path against the "02 Tools" sample
from typing import Annotated
from pydantic import Field
import os, glob


@tool(
    name="file_search",
    description=(
        "Search local documents/notes for a keyword or phrase. Use when the user "
        "asks about content that may live in saved files or exports. Returns "
        "matching snippets with their file names."
    ),
)
def file_search(
    query: Annotated[str, Field(description="Keyword or phrase to search for.")],
    folder: Annotated[str, Field(description="Folder to search in.")] = "./docs",
) -> str:
    """Naive local full-text search over .txt/.md files."""
    print(f"🔧 file_search called: {query!r}")   # remove once confirmed working

    hits = []
    for path in glob.glob(os.path.join(folder, "**", "*"), recursive=True):
        if not path.lower().endswith((".txt", ".md")):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        if query.lower() in text.lower():
            idx = text.lower().find(query.lower())
            start, end = max(0, idx - 80), idx + 120
            snippet = text[start:end].replace("\n", " ").strip()
            hits.append(f"[{os.path.basename(path)}] …{snippet}…")
        if len(hits) >= 5:
            break

    if not hits:
        return f'No local files matched "{query}". State "Data insufficient" to the user.'
    return "Found these matches:\n" + "\n".join(hits)
