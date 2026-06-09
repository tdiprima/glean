"""The agentic loop: plan -> call collectors -> reason -> structured report."""

import json
import logging

from glean.llm import LLM
from glean.prompts import system_prompt
from glean.schemas import REPORT_SCHEMA

logger = logging.getLogger(__name__)

_FINAL_INSTRUCTION = (
    "Stop searching and produce your final report now, as JSON matching the "
    "required schema. Include only claims backed by source URLs seen in tool "
    "results."
)


def _dispatch_tool(name: str, raw_args: str, dispatch: dict) -> str:
    """Execute one collector by name. Returns text for the model."""
    runner = dispatch.get(name)
    if runner is None:
        return f"ERROR: unknown tool {name!r}."
    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError as exc:
        return f"ERROR: could not parse tool arguments: {exc}"
    if not isinstance(args, dict):
        return "ERROR: tool arguments must be an object."
    try:
        return runner(**args)
    except TypeError as exc:  # bad/missing kwargs from the model
        return f"ERROR: invalid arguments for {name}: {exc}"


def investigate(
    llm: LLM,
    *,
    mode: str,
    target: str,
    purpose: str | None,
    max_steps: int,
    dispatch: dict,
    tools: list,
) -> tuple[dict, int]:
    """Run the full investigation. Returns (report_dict, steps_taken)."""
    messages: list[dict] = [
        {"role": "system", "content": system_prompt(mode, target, purpose)},
        {"role": "user", "content": f"Investigate: {target}"},
    ]

    steps = 0
    for steps in range(1, max_steps + 1):
        message = llm.step(messages, tools)

        if not message.tool_calls:
            # Model answered without (more) tools; move to structured report.
            messages.append({"role": "assistant", "content": message.content or ""})
            break

        # Record the assistant turn (with its tool calls) before answering them.
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in message.tool_calls
                ],
            }
        )

        for call in message.tool_calls:
            result = _dispatch_tool(call.function.name, call.function.arguments, dispatch)
            logger.info("tool %s -> %d chars", call.function.name, len(result))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )
    else:
        logger.warning("Reached max_steps=%d; forcing final report.", max_steps)

    messages.append({"role": "user", "content": _FINAL_INSTRUCTION})
    report = llm.structured(messages, REPORT_SCHEMA)
    return report, steps
