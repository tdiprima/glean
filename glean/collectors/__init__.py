"""Collector registry.

Each collector module exposes:
  - TOOL: an OpenAI function-tool schema (dict)
  - run(**kwargs) -> str: executes the collection, returns text for the model

Add a collector by importing it here and adding it to build().
"""

import functools

from glean.collectors import github, web_search, whois
from glean.config import Config


def build(config: Config) -> tuple[dict, list]:
    """Build the dispatch table and tools list, binding config to each runner.

    Returns (dispatch, tools) where dispatch maps tool name -> callable and
    tools is the OpenAI-format tools array. Collectors that need config values
    (e.g. github_token) receive them here via partial application so the model
    cannot supply them.
    """
    dispatch = {
        web_search.TOOL["function"]["name"]: web_search.run,
        github.TOOL["function"]["name"]: functools.partial(
            github.run, github_token=config.github_token
        ),
        whois.TOOL["function"]["name"]: whois.run,
    }
    tools = [web_search.TOOL, github.TOOL, whois.TOOL]
    return dispatch, tools
