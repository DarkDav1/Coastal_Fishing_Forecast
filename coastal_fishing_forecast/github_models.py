"""GitHub Models adapter for planner text generation."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping
from urllib.request import Request, urlopen


GITHUB_MODELS_ENDPOINT = "https://models.github.ai/inference/chat/completions"
GITHUB_MODELS_DEFAULT_MODEL = "openai/gpt-4o-mini"
GITHUB_TOKEN_ENV = "GITHUB_TOKEN"
GITHUB_MODELS_MODEL_ENV = "GITHUB_MODELS_MODEL"
GITHUB_MODELS_ENDPOINT_ENV = "GITHUB_MODELS_ENDPOINT"


class GitHubModelsError(RuntimeError):
    """Raised when GitHub Models cannot produce a usable planner response."""


def _planner_prompt(payload: Mapping[str, Any]) -> str:
    return (
        "Create concise JSON for a fishing action plan from the provided forecast fields. "
        "Do not invent locations, species, scores, water types, or weather facts. "
        "Do not modify the forecast score, best window, confidence, support status, or tide status. "
        "Use terrain_certainty strictly: do not mention any forbidden_claims. Only claim a public jetty, pier, "
        "or wharf when it appears in confirmed_features. Never treat a boat ramp as a public jetty. "
        "Only return JSON with optional text fields for recommendation_summary, primary_action_text, "
        "backup_action_text, avoid, risks, confidence_note, and data_source_note.\n\n"
        f"Forecast fields:\n{json.dumps(payload, sort_keys=True)}"
    )


def _explanation_prompt(payload: Mapping[str, Any]) -> str:
    return (
        "Rewrite the provided fishing forecast evidence into concise user-facing explanation text. "
        "Use only the provided fields. Do not invent locations, structures, species, weather facts, tide facts, "
        "scores, or water types. Do not modify any score, best window, confidence, support status, tide status, "
        "or risk warning. Explain in plain language which real-world conditions helped the window and which "
        "conditions held it back. If weather_trend.change_notes are provided, use them to explain concrete "
        "weather changes such as cooling, pressure movement, wind shifts, rain, gusts, or sea-state changes. "
        "Do not discuss the scoring system, formulas, rules, tags, raw signals, "
        "internal fields, or model mechanics. "
        "Only return JSON with optional fields: why_this_window, score_story, local_adjustment_summary. "
        "Do not return the original input objects. why_this_window must be a list of 2 to 4 short strings.\n\n"
        f"Forecast explanation fields:\n{json.dumps(payload, sort_keys=True)}"
    )


def _extract_content(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise GitHubModelsError("GitHub Models response did not include choices.")
    message = choices[0].get("message") if isinstance(choices[0], Mapping) else None
    content = message.get("content") if isinstance(message, Mapping) else None
    if not isinstance(content, str) or not content.strip():
        raise GitHubModelsError("GitHub Models response did not include text content.")
    return content.strip()


def generate_github_models_plan_text(
    payload: Mapping[str, Any],
    *,
    token: str | None = None,
    model: str | None = None,
    endpoint: str | None = None,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    resolved_token = token or os.environ.get(GITHUB_TOKEN_ENV)
    if not resolved_token:
        raise GitHubModelsError(f"Missing {GITHUB_TOKEN_ENV}.")

    resolved_model = model or os.environ.get(GITHUB_MODELS_MODEL_ENV) or GITHUB_MODELS_DEFAULT_MODEL
    resolved_endpoint = endpoint or os.environ.get(GITHUB_MODELS_ENDPOINT_ENV) or GITHUB_MODELS_ENDPOINT
    body = {
        "model": resolved_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You rewrite structured fishing forecast data into cautious action-plan text. Return JSON only.",
            },
            {"role": "user", "content": _planner_prompt(payload)},
        ],
    }
    request = Request(
        resolved_endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resolved_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    content = _extract_content(response_payload)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise GitHubModelsError("GitHub Models returned non-JSON planner content.") from exc
    if not isinstance(parsed, dict):
        raise GitHubModelsError("GitHub Models planner content must be a JSON object.")
    return parsed


def generate_github_models_explanation_text(
    payload: Mapping[str, Any],
    *,
    token: str | None = None,
    model: str | None = None,
    endpoint: str | None = None,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    resolved_token = token or os.environ.get(GITHUB_TOKEN_ENV)
    if not resolved_token:
        raise GitHubModelsError(f"Missing {GITHUB_TOKEN_ENV}.")

    resolved_model = model or os.environ.get(GITHUB_MODELS_MODEL_ENV) or GITHUB_MODELS_DEFAULT_MODEL
    resolved_endpoint = endpoint or os.environ.get(GITHUB_MODELS_ENDPOINT_ENV) or GITHUB_MODELS_ENDPOINT
    body = {
        "model": resolved_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You rewrite structured fishing forecast evidence into cautious explanation text. Return JSON only.",
            },
            {"role": "user", "content": _explanation_prompt(payload)},
        ],
    }
    request = Request(
        resolved_endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resolved_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    content = _extract_content(response_payload)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise GitHubModelsError("GitHub Models returned non-JSON explanation content.") from exc
    if not isinstance(parsed, dict):
        raise GitHubModelsError("GitHub Models explanation content must be a JSON object.")
    return parsed
