"""Optional real-LLM hook for AutoFlow.

The demo runs entirely on template + rule agents with no API key, so
it works offline and costs nothing. When a key IS configured, this
module calls Google's Gemini API directly with the standard library
(no extra SDK dependency):

  AUTOFLOW_LLM_PROVIDER=gemini
  AUTOFLOW_LLM_API_KEY=<key kept in the deployment env vars only>

The model is gemini-3-flash-preview (verified working 2026-10-25;
gemini-2.5-flash was retired for new accounts, and gemini-3.8-flash
was returning high-demand errors that day).

Security rules, by design:
  - The key is read ONLY from the environment, never from a file,
    never from the repo, and never logged or returned by any API.
  - With no provider/key configured, status() reports disabled and
    generate() returns an honest disabled result; agents keep using
    the template implementation, so the demo never breaks.
  - The live Render backend cannot read Muse's stored credential;
    to enable Gemini live, set the two env vars above in the Render
    dashboard (Environment tab) and redeploy. The key must never be
    committed to the public repo.
"""
import json
import os
import urllib.error
import urllib.request

SUPPORTED = ("openai", "gemini")
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def status() -> dict:
    provider = os.environ.get("AUTOFLOW_LLM_PROVIDER", "").lower()
    enabled = provider in SUPPORTED and bool(
        os.environ.get("AUTOFLOW_LLM_API_KEY")
    )
    return {
        "enabled": enabled,
        "provider": provider if provider in SUPPORTED else None,
        "model": GEMINI_MODEL if provider == "gemini" else None,
        "fallback": "template_agents",
        "note": "No API key is configured in the demo, so template "
        "agents answer. Set AUTOFLOW_LLM_PROVIDER=gemini and "
        "AUTOFLOW_LLM_API_KEY in the deployment env vars to "
        "enable a real LLM.",
    }


def generate(prompt: str) -> dict:
    """Generate one short reply with the configured provider.

    Returns {"ok": True, "text": ...} on success, or
    {"ok": False, "error": ...} with an honest reason (disabled,
    unsupported provider, or the provider's error) and no key value.
    """
    provider = os.environ.get("AUTOFLOW_LLM_PROVIDER", "").lower()
    key = os.environ.get("AUTOFLOW_LLM_API_KEY", "")
    if provider not in SUPPORTED or not key:
        return {"ok": False, "error": "llm_disabled",
                "detail": "No LLM provider/key configured; template agents answer."}
    if provider != "gemini":
        return {"ok": False, "error": "unsupported_provider",
                "detail": "Only gemini is implemented in this hook."}
    body = json.dumps(
        {"contents": [{"parts": [{"text": prompt}]}]}).encode()
    request = urllib.request.Request(GEMINI_URL, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("X-Goog-Api-Key", key)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode()).get("error", {}).get(
                "message", f"HTTP {exc.code}")
        except Exception:
            detail = f"HTTP {exc.code}"
        return {"ok": False, "error": "provider_error", "detail": detail}
    except Exception as exc:  # network/timeout: never crash the caller
        return {"ok": False, "error": "request_failed", "detail": str(exc)}
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return {"ok": False, "error": "unexpected_response",
                "detail": "Provider returned no text."}
    return {"ok": True, "provider": "gemini", "model": GEMINI_MODEL,
            "text": text}
