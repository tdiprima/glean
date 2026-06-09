"""Domain WHOIS collector. Useful for company due diligence (age, registrar)."""

import logging

logger = logging.getLogger(__name__)

TOOL = {
    "type": "function",
    "function": {
        "name": "domain_whois",
        "description": (
            "Look up public WHOIS registration data for a domain (registrar, "
            "creation/expiry dates, registrant org/country where public). "
            "Useful to gauge a company's web presence and age."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Bare domain, e.g. example.com",
                }
            },
            "required": ["domain"],
        },
    },
}


def _clean(domain: str) -> str:
    """Strip scheme, path, and leading www from a user-supplied domain."""
    value = (domain or "").strip().lower()
    for prefix in ("https://", "http://"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    value = value.split("/", 1)[0]
    if value.startswith("www."):
        value = value[4:]
    return value


def run(domain: str) -> str:
    """Run a WHOIS lookup. Returns formatted public fields or an error string."""
    target = _clean(domain)
    if not target or "." not in target:
        return f"ERROR: not a valid domain: {domain!r}"

    try:
        import whois  # python-whois

        data = whois.whois(target)
    except Exception as exc:  # boundary: report to model, don't crash
        logger.warning("domain_whois failed for %r: %s", target, exc)
        return f"ERROR: WHOIS lookup failed: {exc}"

    fields = {
        "Registrar": data.get("registrar"),
        "Created": data.get("creation_date"),
        "Expires": data.get("expiration_date"),
        "Org": data.get("org"),
        "Country": data.get("country"),
        "Name servers": data.get("name_servers"),
    }
    lines = [f"WHOIS for {target}:"]
    for key, value in fields.items():
        if value:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines) if len(lines) > 1 else f"No public WHOIS data for {target}."
