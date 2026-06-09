"""Ethics gate. Enforced in code, not just documented.

Refuses disallowed targets and purposes before any collection runs. This is a
coarse first line of defense; the system prompt adds a second LLM-side refusal
layer. Neither is a substitute for the operator's lawful, ethical intent.
"""

import re

# Phrasings that indicate stalking, harm, or locating someone against their will.
_DISALLOWED_INTENT = [
    r"\bstalk(ing|er)?\b",
    r"\bharass(ing|ment)?\b",
    r"\bintimidat",
    r"\bhunt (him|her|them) down\b",
    r"\btrack (his|her|their) (live |real[- ]time )?location\b",
    r"\bwhere (does|is) .*(hiding|live[s]?)\b",
    r"\bget (revenge|back at)\b",
    r"\bhurt\b",
    r"\bblackmail\b",
    r"\bdox(x)?(ing)?\b",
]

# Phrasings that indicate the target is a minor.
_MINOR_TARGET = [
    r"\bminor\b",
    r"\bunder ?-?18\b",
    r"\bunderage\b",
    r"\b(my|the|a|this) (child|kid|son|daughter)\b",
    r"\bteenager?\b",
    r"\bhigh[- ]school student\b",
]


class EthicsViolation(ValueError):
    """Raised when a query or purpose fails the ethics gate."""


def _matches_any(text: str, patterns: list[str]) -> str | None:
    """Return the first pattern that matches, or None."""
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return pattern
    return None


def check(mode: str, target: str, purpose: str | None) -> None:
    """Validate a request. Raises EthicsViolation if it must be refused.

    Person mode requires a stated lawful purpose. Disallowed-intent and
    minor-target phrasings are refused in any mode.
    """
    if not target or not target.strip():
        raise EthicsViolation("Target must not be empty.")

    haystack = f"{target} {purpose or ''}"

    hit = _matches_any(haystack, _DISALLOWED_INTENT)
    if hit:
        raise EthicsViolation(
            "Refused: the request appears to involve stalking, harassment, "
            "doxxing, locating someone against their will, or causing harm. "
            "GLEAN supports only lawful, public-source due diligence."
        )

    hit = _matches_any(haystack, _MINOR_TARGET)
    if hit:
        raise EthicsViolation(
            "Refused: GLEAN will not build a profile of a minor."
        )

    if mode == "person":
        if not purpose or len(purpose.strip()) < 8:
            raise EthicsViolation(
                "Person mode requires a clear lawful purpose via --purpose "
                '(e.g. --purpose "vetting a prospective business partner").'
            )
