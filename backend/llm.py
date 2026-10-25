"""Optional LLM hook for AutoFlow.

The demo runs entirely on template + rule agents with no API key, so
it works offline and costs nothing. This module is the single place
where a real LLM would be plugged in later:

  - Set AUTOFLOW_LLM_PROVIDER=openai (or gemini) and the matching
    API key env var, then implement _call_provider() with that
    provider's SDK. The agents keep the same return shape
    (draft + source + steps), so no dashboard or API code changes.
  - With no provider/key configured, status() reports disabled and
    every agent falls back to the template implementation.

No key is ever read, logged, or stored by this module; it only
reports whether a provider name is configured.
"""
import os

SUPPORTED = ("openai", "gemini")


def status() -> dict:
    provider = os.environ.get("AUTOFLOW_LLM_PROVIDER", "").lower()
    enabled = provider in SUPPORTED and bool(
        os.environ.get("AUTOFLOW_LLM_API_KEY")
    )
    return {
        "enabled": enabled,
        "provider": provider if provider in SUPPORTED else None,
        "fallback": "template_agents",
        "note": "No API key is configured in the demo, so template "
        "agents answer. Set AUTOFLOW_LLM_PROVIDER and "
        "AUTOFLOW_LLM_API_KEY to enable a real LLM.",
    }
