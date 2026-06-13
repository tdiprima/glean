"""Collector registry.

Each collector module exposes:
  - TOOL: an OpenAI function-tool schema (dict)
  - run(**kwargs) -> str: executes the collection, returns text for the model

Add a collector by importing it here and adding it to _COLLECTORS and build().
"""

import functools

from glean.collectors import court_records, github, news, web_search, whois
from glean.config import Config

_COLLECTORS = [web_search, news, github, whois, court_records]


def _validate_collector(module) -> None:
    """Raise TypeError if module does not satisfy the collector protocol."""
    name = getattr(module, "__name__", repr(module))
    if not isinstance(getattr(module, "TOOL", None), dict):
        raise TypeError(f"Collector {name!r}: TOOL must be a dict")
    if not callable(getattr(module, "run", None)):
        raise TypeError(f"Collector {name!r}: run must be callable")


def build(config: Config) -> tuple[dict, list]:
    """Build the dispatch table and tools list, binding config to each runner.

    Validates every registered collector at startup. Raises TypeError on the
    first collector that does not expose TOOL (dict) and run (callable).

    Returns (dispatch, tools) where dispatch maps tool name -> callable and
    tools is the OpenAI-format tools array. Collectors that need config values
    (e.g. github_token) receive them here via partial application so the model
    cannot supply them.
    """
    for module in _COLLECTORS:
        _validate_collector(module)

    dispatch = {
        web_search.TOOL["function"]["name"]: web_search.run,
        news.TOOL["function"]["name"]: news.run,
        github.TOOL["function"]["name"]: functools.partial(
            github.run, github_token=config.github_token
        ),
        whois.TOOL["function"]["name"]: whois.run,
        court_records.TOOL["function"]["name"]: functools.partial(
            court_records.run, courtlistener_token=config.courtlistener_token
        ),
    }
    tools = [module.TOOL for module in _COLLECTORS]
    return dispatch, tools
