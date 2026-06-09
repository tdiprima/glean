"""JSON schema for the final structured report.

Used with OpenAI structured outputs (strict mode) so the synthesizer always
returns a parseable object. Strict mode requires every property listed in
`required` and `additionalProperties: false` on every object.
"""

REPORT_SCHEMA = {
    "name": "osint_report",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {
                "type": "string",
                "description": "Plain-language overview of the findings.",
            },
            "findings": {
                "type": "array",
                "description": "Discrete factual findings, each backed by a source.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "claim": {"type": "string"},
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "source_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["claim", "confidence", "source_urls"],
                },
            },
            "red_flags": {
                "type": "array",
                "description": "Concerns the operator should weigh. May be empty.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "concern": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "source_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["concern", "severity", "source_urls"],
                },
            },
            "recommendation": {
                "type": "string",
                "description": "Balanced, non-determinative guidance for the operator.",
            },
            "sources": {
                "type": "array",
                "description": "All distinct source URLs consulted.",
                "items": {"type": "string"},
            },
        },
        "required": [
            "summary",
            "findings",
            "red_flags",
            "recommendation",
            "sources",
        ],
    },
}
