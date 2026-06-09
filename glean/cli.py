"""GLEAN command-line entry point. Orchestration only."""

import argparse
import logging
import sys

from glean import audit, ethics, report
from glean.agent import investigate
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
        "--purpose",
        default=None,
        help="Lawful purpose. Required for person mode.",
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

    # Ethics gate — refuse disallowed targets before any collection runs.
    try:
        ethics.check(args.mode, args.target, args.purpose)
    except ethics.EthicsViolation as exc:
        print(str(exc), file=sys.stderr)
        audit.init_db(config.db_path)
        audit.record(
            config.db_path,
            mode=args.mode,
            target=args.target,
            purpose=args.purpose,
            steps=0,
            status="refused",
        )
        return 3

    audit.init_db(config.db_path)
    llm = LLM(api_key=config.openai_api_key, model=config.model)

    try:
        data, steps = investigate(
            llm,
            mode=args.mode,
            target=args.target,
            purpose=args.purpose,
            max_steps=config.max_steps,
        )
    except Exception as exc:  # top-level boundary: log, audit, surface cleanly
        logging.getLogger("glean").exception("Investigation failed")
        audit.record(
            config.db_path,
            mode=args.mode,
            target=args.target,
            purpose=args.purpose,
            steps=0,
            status="error",
        )
        print(f"Investigation failed: {exc}", file=sys.stderr)
        return 1

    audit.record(
        config.db_path,
        mode=args.mode,
        target=args.target,
        purpose=args.purpose,
        steps=steps,
        status="ok",
    )

    markdown = report.to_markdown(
        data, mode=args.mode, target=args.target, purpose=args.purpose
    )

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
