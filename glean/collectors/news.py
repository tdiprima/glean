"""News collector using DuckDuckGo news search — no API key required."""

import logging

logger = logging.getLogger(__name__)

TOOL = {
    "type": "function",
    "function": {
        "name": "news_search",
        "description": (
            "Search recent news articles about a person, company, or topic. "
            "Returns titles, sources, dates, URLs, and snippets. "
            "Useful for recent events, controversies, press coverage, or announcements."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The news search query.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "How many articles to return (1-10).",
                },
            },
            "required": ["query"],
        },
    },
}

_MAX_ALLOWED = 10


def run(query: str, max_results: int = 5) -> str:
    """Search news via DuckDuckGo. Returns formatted articles or an error string."""
    if not query or not query.strip():
        return "ERROR: empty query."

    count = max(1, min(int(max_results), _MAX_ALLOWED))

    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=count))
    except Exception as exc:
        logger.warning("news_search failed for %r: %s", query, exc)
        return f"ERROR: news search failed: {exc}"

    if not results:
        return f"No news results for {query!r}."

    lines = []
    for item in results:
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        source = item.get("source", "").strip()
        date = item.get("date", "").strip()
        body = item.get("body", "").strip()
        lines.append(f"- [{source}] {title} ({date})\n  {url}\n  {body}")

    return "\n".join(lines)
