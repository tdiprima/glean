"""GLEAN command-line entry point. Orchestration only."""

import argparse
import logging
import sys
import time

from glean import ethics, report
from glean.agent import investigate
from glean.audit import Auditor
from glean.collectors import build as build_collectors
from glean.config import ConfigError, load_config
from glean.llm import LLM


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="glean",
        description="AI-native, ethics-gated OSINT for due diligence.",
    )
    parser.add_argument("target", help="Company name, person name, or handle.")
    parser.add_argument(
        "--mode",
        choices=["company", "person"],
        default="company",
        help="Investigation mode (default: company).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write the markdown report to this file (default: stdout).",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable info-level logging."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run GLEAN. Returns a process exit code."""
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    auditor = Auditor(config.db_path)

    # Ethics gate — refuse disallowed targets before any collection runs.
    try:
        ethics.check(args.mode, args.target)
    except ethics.EthicsViolation as exc:
        print(str(exc), file=sys.stderr)
        auditor.record(
            mode=args.mode,
            target=args.target,
            steps=0,
            status="refused",
        )
        return 3

    llm = LLM(api_key=config.openai_api_key, model=config.model)
    dispatch, tools = build_collectors(config)

    start = time.monotonic()
    try:
        data, steps = investigate(
            llm,
            mode=args.mode,
            target=args.target,
            max_steps=config.max_steps,
            dispatch=dispatch,
            tools=tools,
        )
    except KeyboardInterrupt:
        duration_s = time.monotonic() - start
        print("\nCancelled.", file=sys.stderr)
        auditor.record(
            mode=args.mode,
            target=args.target,
            steps=0,
            status="cancelled",
            duration_s=duration_s,
        )
        return 130  # standard shell convention for SIGINT
    except Exception as exc:  # top-level boundary: log, audit, surface cleanly
        duration_s = time.monotonic() - start
        logging.getLogger("glean").exception("Investigation failed")
        auditor.record(
            mode=args.mode,
            target=args.target,
            steps=0,
            status="error",
            duration_s=duration_s,
        )
        print(f"Investigation failed: {exc}", file=sys.stderr)
        return 1

    duration_s = time.monotonic() - start
    auditor.record(
        mode=args.mode,
        target=args.target,
        steps=steps,
        status="ok",
        duration_s=duration_s,
    )
    print(f"Completed in {duration_s:.1f}s ({steps} steps).", file=sys.stderr)

    markdown = report.to_markdown(data, mode=args.mode, target=args.target)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(markdown)
        except OSError as exc:
            print(f"Could not write {args.output}: {exc}", file=sys.stderr)
            return 1
        print(f"Report written to {args.output}")
    else:
        print(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
