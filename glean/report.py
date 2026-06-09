"""Render a structured report dict into markdown."""

from datetime import datetime, timezone


def _bullet_sources(urls: list[str]) -> str:
    """Format a list of source URLs inline."""
    if not urls:
        return "_(no source)_"
    return ", ".join(urls)


def to_markdown(report: dict, *, mode: str, target: str, purpose: str | None) -> str:
    """Build a markdown document from the report object."""
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# GLEAN report — {target}",
        "",
        f"- **Mode:** {mode}",
    ]
    if purpose:
        lines.append(f"- **Stated purpose:** {purpose}")
    lines += [
        f"- **Generated:** {generated}",
        "",
        "> Public-source intelligence. Not for FCRA-covered eligibility "
        "decisions. Verify before acting.",
        "",
        "## Summary",
        "",
        report.get("summary", "_(none)_"),
        "",
        "## Findings",
        "",
    ]

    findings = report.get("findings", [])
    if findings:
        for item in findings:
            lines.append(
                f"- **[{item.get('confidence', '?')}]** {item.get('claim', '')}  "
                f"\n  Sources: {_bullet_sources(item.get('source_urls', []))}"
            )
    else:
        lines.append("_No findings._")

    lines += ["", "## Red flags", ""]
    red_flags = report.get("red_flags", [])
    if red_flags:
        for item in red_flags:
            lines.append(
                f"- **[{item.get('severity', '?')}]** {item.get('concern', '')}  "
                f"\n  Sources: {_bullet_sources(item.get('source_urls', []))}"
            )
    else:
        lines.append("_None identified._")

    lines += [
        "",
        "## Recommendation",
        "",
        report.get("recommendation", "_(none)_"),
        "",
        "## Sources",
        "",
    ]
    sources = report.get("sources", [])
    if sources:
        lines += [f"- {url}" for url in sources]
    else:
        lines.append("_No sources recorded._")

    lines.append("")
    return "\n".join(lines)
