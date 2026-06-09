"""Public web search collector (DuckDuckGo via ddgs — no API key required)."""

import logging

logger = logging.getLogger(__name__)

TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the public web for information about a person, company, or "
            "topic. Returns titles, URLs, and snippets. Use specific queries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "How many results to return (1-10).",
                },
            },
            "required": ["query"],
        },
    },
}

_MAX_ALLOWED = 10


def run(query: str, max_results: int = 5) -> str:
    """Run a public web search. Returns formatted results or an error string."""
    if not query or not query.strip():
        return "ERROR: empty query."

    count = max(1, min(int(max_results), _MAX_ALLOWED))

    try:
        # Imported lazily so the package imports even if ddgs is absent.
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=count))
    except Exception as exc:  # collector boundary: report to model, don't crash
        logger.warning("web_search failed for %r: %s", query, exc)
        return f"ERROR: web search failed: {exc}"

    if not results:
        return f"No results for {query!r}."

    lines = []
    for item in results:
        title = item.get("title", "").strip()
        href = item.get("href", "").strip()
        body = item.get("body", "").strip()
        lines.append(f"- {title}\n  {href}\n  {body}")
    return "\n".join(lines)
