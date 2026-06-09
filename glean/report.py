"""Render a structured report dict into markdown."""

from datetime import datetime, timezone


def _bullet_sources(urls: list[str]) -> str:
    """Format a list of source URLs inline."""
    if not urls:
        return "_(no source)_"
    return ", ".join(urls)


def to_markdown(report: dict, *, mode: str, target: str, purpose: str | None) -> str:
    """Build a markdown document from the report object.

    report must be a validated dict matching REPORT_SCHEMA — all required keys
    (summary, findings, red_flags, recommendation, sources) must be present.
    Raises KeyError if any required key is missing.
    """
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
        report["summary"],
        "",
        "## Findings",
        "",
    ]

    findings = report["findings"]
    if findings:
        for item in findings:
            lines.append(
                f"- **[{item['confidence']}]** {item['claim']}  "
                f"\n  Sources: {_bullet_sources(item['source_urls'])}"
            )
    else:
        lines.append("_No findings._")

    lines += ["", "## Red flags", ""]
    red_flags = report["red_flags"]
    if red_flags:
        for item in red_flags:
            lines.append(
                f"- **[{item['severity']}]** {item['concern']}  "
                f"\n  Sources: {_bullet_sources(item['source_urls'])}"
            )
    else:
        lines.append("_None identified._")

    lines += [
        "",
        "## Recommendation",
        "",
        report["recommendation"],
        "",
        "## Sources",
        "",
    ]
    sources = report["sources"]
    if sources:
        lines += [f"- {url}" for url in sources]
    else:
        lines.append("_No sources recorded._")

    lines.append("")
    return "\n".join(lines)
