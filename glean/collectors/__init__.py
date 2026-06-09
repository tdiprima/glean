"""Collector registry.

Each collector module exposes:
  - TOOL: an OpenAI function-tool schema (dict)
  - run(**kwargs) -> str: executes the collection, returns text for the model

Add a collector by importing it here and adding it to COLLECTORS.
"""

from glean.collectors import github, web_search, whois

COLLECTORS = [web_search, github, whois]

# name -> run callable
DISPATCH = {module.TOOL["function"]["name"]: module.run for module in COLLECTORS}

# OpenAI tools array
TOOLS = [module.TOOL for module in COLLECTORS]
