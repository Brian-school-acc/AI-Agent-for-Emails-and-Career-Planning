"""Custom tools for the agents. Each function is decorated with @tool
so the framework exposes it. Import these into server.py and attach via tools=[...]."""

import os, glob

from agent_framework import tool
from typing import Annotated
from pydantic import Field
from random import randint
from datetime import datetime
from zoneinfo import ZoneInfo

# Import the DuckDuckGo Search Client
# from duckduckgo_search import DDGS

@tool(approval_mode="never_require")
def summarize_document(document_id: str) -> str:
    """
    Retrieve a brief summary of a specific document by its ID or title.

    Args:
        document_id: The exact title or ID of the document to summarize.
    """
    return f"Summary of {document_id}: This document outlines the standard operating procedures and academic requirements for the current semester. It includes important dates, grading rubrics, and contact protocols."

# @tool(approval_mode="never_require")
# def search_the_web(
#     query: Annotated[str, Field(description="The clear search phrase or keyword string to look up on the open web.")],
#     max_results: Annotated[int, Field(description="The maximum number of search entries to pull back.")] = 5
# ) -> str:
#     """Search the internet using DuckDuckGo to look up real-time information, current facts, or public data."""
#     try:
#         # Context manager handles instantiation and automatic connection teardown safely
#         with DDGS() as ddgs:
#             search_generator = ddgs.text(keywords=query, max_results=max_results)
#             results = list(search_generator)

#         if not results:
#             return f"The search returned no active results on the internet for '{query}'."

#         formatted_results = []
#         for idx, item in enumerate(results, start=1):
#             title = item.get("title", "Untitled")
#             link = item.get("href", "No Link Available")
#             snippet = item.get("body", "No Description Available")
            
#             formatted_results.append(f"[{idx}] Source: {title}\nURL: {link}\nContent: {snippet}")

#         return f"Live Web Results for '{query}':\n\n" + "\n\n".join(formatted_results)

#     except Exception as e:
#         return f"The web search tool encountered an external error: {str(e)}"

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
