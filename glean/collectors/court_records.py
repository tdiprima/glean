"""CourtListener collector — searches public federal court records via REST API.

Free registration at https://www.courtlistener.com/ provides a token that raises
rate limits from 5 000 to 30 000 requests/day. The token is optional; unauthenticated
requests still work for moderate usage.

Set COURTLISTENER_TOKEN in the environment to authenticate.
"""

import logging

import requests

logger = logging.getLogger(__name__)

_API_BASE = "https://www.courtlistener.com/api/rest/v4"
_SITE_BASE = "https://www.courtlistener.com"
_TIMEOUT = 10

# Supported result types and their human-readable labels.
_RESULT_TYPES = {
    "o": "opinion",
    "r": "PACER document",
}

TOOL = {
    "type": "function",
    "function": {
        "name": "court_records_search",
        "description": (
            "Search public U.S. federal court records via CourtListener. "
            "Returns case names, courts, filing dates, docket numbers, and links. "
            "Covers opinions and PACER documents. "
            "Useful for litigation history, judgments, or regulatory actions "
            "involving a person or company."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Full-text search query, e.g. a person's name, company name, "
                        "or legal topic. Supports boolean operators (AND, OR, NOT)."
                    ),
                },
                "result_type": {
                    "type": "string",
                    "enum": ["o", "r"],
                    "description": (
                        "'o' for court opinions (default), "
                        "'r' for PACER/RECAP case documents."
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10).",
                },
            },
            "required": ["query"],
        },
    },
}

_MAX_ALLOWED = 10


def _headers(token: str | None) -> dict[str, str]:
    """Build request headers, including auth only when a token is provided."""
    headers = {"User-Agent": "glean-osint"}
    if token:
        headers["Authorization"] = f"Token {token}"
    return headers


def _format_opinion(item: dict) -> str:
    case_name = item.get("caseName", "").strip()
    court = item.get("court", "").strip()
    date_filed = item.get("dateFiled", "").strip()
    docket_number = item.get("docketNumber", "").strip()
    status = item.get("status", "").strip()
    slug = item.get("absolute_url", "").strip()
    url = f"{_SITE_BASE}{slug}" if slug else ""

    parts = [f"- {case_name or '(unnamed)'}"]
    if court:
        parts.append(f"  Court: {court}")
    if docket_number:
        parts.append(f"  Docket: {docket_number}")
    if date_filed:
        parts.append(f"  Filed: {date_filed}")
    if status:
        parts.append(f"  Status: {status}")
    if url:
        parts.append(f"  {url}")
    return "\n".join(parts)


def _format_recap(item: dict) -> str:
    case_name = item.get("caseName", "").strip()
    court = item.get("court", "").strip()
    date_filed = item.get("dateFiled", "").strip()
    docket_number = item.get("docketNumber", "").strip()
    description = item.get("description", "").strip()
    slug = item.get("absolute_url", "").strip()
    url = f"{_SITE_BASE}{slug}" if slug else ""

    parts = [f"- {case_name or '(unnamed)'}"]
    if court:
        parts.append(f"  Court: {court}")
    if docket_number:
        parts.append(f"  Docket: {docket_number}")
    if date_filed:
        parts.append(f"  Filed: {date_filed}")
    if description:
        parts.append(f"  Description: {description[:200]}")
    if url:
        parts.append(f"  {url}")
    return "\n".join(parts)


_FORMATTERS = {"o": _format_opinion, "r": _format_recap}


def run(
    query: str,
    result_type: str = "o",
    max_results: int = 5,
    *,
    courtlistener_token: str | None = None,
) -> str:
    """Search CourtListener. Returns formatted results or an error string."""
    if not query or not query.strip():
        return "ERROR: empty query."

    if result_type not in _RESULT_TYPES:
        return f"ERROR: result_type must be one of {list(_RESULT_TYPES.keys())!r}."

    count = max(1, min(int(max_results), _MAX_ALLOWED))

    try:
        response = requests.get(
            f"{_API_BASE}/search/",
            headers=_headers(courtlistener_token),
            params={"q": query, "type": result_type, "order_by": "score desc", "page_size": count},
            timeout=_TIMEOUT,
        )
        if response.status_code == 401:
            return "ERROR: CourtListener authentication failed. Check COURTLISTENER_TOKEN."
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.warning("court_records_search failed for %r: %s", query, exc)
        return f"ERROR: CourtListener request failed: {exc}"

    results = data.get("results", [])
    if not results:
        return f"No {_RESULT_TYPES[result_type]} records found for {query!r}."

    formatter = _FORMATTERS[result_type]
    count_label = _RESULT_TYPES[result_type]
    header = f"CourtListener {count_label} results for {query!r}:"
    body = "\n\n".join(formatter(item) for item in results[:count])
    return f"{header}\n\n{body}"
