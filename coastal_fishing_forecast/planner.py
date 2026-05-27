"""Fishing action-plan generation from frontend forecast payloads."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from coastal_fishing_forecast.github_models import GitHubModelsError, generate_github_models_plan_text


PLAN_CONTRACT_VERSION = "2026-04-28.fishing_plan.v1"
SUPPORTED_PLANNER_PROVIDERS = {"rule_based", "llm", "github_models"}
MODEL_TEXT_FIELDS = {
    "recommendation_summary",
    "primary_action_text",
    "backup_action_text",
    "avoid",
    "risks",
    "confidence_note",
    "data_source_note",
}
UNCONFIRMED_PUBLIC_JETTY_TERMS = {
    "jetty",
    "jetties",
    "pier",
    "piers",
    "wharf",
    "wharves",
    "public jetty",
    "public pier",
    "public wharf",
}
UNCONFIRMED_STRUCTURE_TERMS = {
    *UNCONFIRMED_PUBLIC_JETTY_TERMS,
    "boat ramp",
    "boat ramps",
    "breakwall",
    "breakwalls",
    "breakwater",
    "breakwaters",
    "marina",
    "marinas",
    "structure fish",
}
PUBLIC_JETTY_FEATURE_KEYS = {
    "jetty",
    "jetty_wharf",
    "pier",
    "wharf",
    "public_jetty",
    "public_pier",
    "public_wharf",
}
STRUCTURE_FEATURE_KEYS = {
    *PUBLIC_JETTY_FEATURE_KEYS,
    "boat_ramp",
    "breakwall",
    "breakwater",
    "marina",
}
PUBLIC_ACCESS_VALUES = {"public", "yes", "permissive", "designated"}
PUBLIC_STRUCTURE_LABELS = {
    "public_jetty": "mapped public jetty",
    "public_pier": "mapped public pier",
    "public_wharf": "mapped public wharf",
    "fishing_platform": "mapped public fishing platform",
    "rocky_shoreline": "mapped rocky shoreline",
}
PRIMARY_PUBLIC_STRUCTURE_KEYS = ("public_jetty", "public_pier", "public_wharf", "fishing_platform")
BACKUP_PUBLIC_STRUCTURE_KEYS = ("rocky_shoreline", "fishing_platform", "public_jetty", "public_pier", "public_wharf")
WATER_TYPE_LABELS = {
    "bay_estuary_edge": "bay / estuary edge",
    "estuary_edge": "estuary edge",
    "bay_edge": "bay edge",
    "channel_edge": "channel edge",
    "surf_beach": "surf beach",
    "open_rocks": "open rocks",
    "beach": "beach",
    "rocks": "rocks",
    "jetty": "inferred structure-style edge",
    "jetty_wharf": "inferred structure-style edge",
}


def _recommendation(score: int | None, confidence_label: str) -> dict[str, Any]:
    if score is None:
        return {
            "label": "skip",
            "score": None,
            "summary": "This location is outside the current coastal and tidal forecast scope.",
        }
    if confidence_label == "low":
        return {
            "label": "maybe",
            "score": score,
            "summary": "Treat this as a cautious nearby preview, not a confirmed spot recommendation.",
        }
    if score >= 65:
        return {
            "label": "go",
            "score": score,
            "summary": "Conditions support a useful nearby fishing window.",
        }
    if score >= 45:
        return {
            "label": "maybe",
            "score": score,
            "summary": "There are usable nearby options, but keep a backup plan.",
        }
    return {
        "label": "skip",
        "score": score,
        "summary": "The current preview is weak enough that waiting or moving location is the safer plan.",
    }


def _safe_water_type_text(raw_water_type: Any) -> str:
    if raw_water_type is None:
        return "leading nearby water-type"
    text = WATER_TYPE_LABELS.get(str(raw_water_type), str(raw_water_type))
    if _contains_forbidden_claim(text, UNCONFIRMED_STRUCTURE_TERMS):
        return "inferred structure-style edge"
    return text


def _primary_action(best_window: Mapping[str, Any] | None, confidence_label: str) -> dict[str, Any] | None:
    if best_window is None:
        return None
    prefix = "Use as a lower-confidence preview: " if confidence_label == "low" else ""
    water_type = best_window.get("dominant_water_type")
    water_type_text = _safe_water_type_text(water_type)
    time_window = best_window.get("time_window")
    return {
        "time_window": time_window,
        "representative_time": best_window.get("representative_time"),
        "water_type": water_type,
        "score": best_window.get("score"),
        "text": (
            f"{prefix}start with the {water_type_text} signal during {time_window}. "
            "Fish the first readable edge for about 60-90 minutes, then reassess rather than forcing the spot."
        ),
    }


def _backup_action(explanation: Mapping[str, Any]) -> dict[str, Any] | None:
    alternatives = explanation.get("alternatives") or []
    if not alternatives:
        return None
    first = alternatives[0]
    water_type_text = _safe_water_type_text(first.get("label"))
    return {
        "water_type": first.get("label"),
        "score": first.get("score"),
        "text": f"Backup option: consider the {water_type_text} if the first choice looks poor on arrival.",
    }


def _avoid(best_window: Mapping[str, Any] | None, risks: list[str]) -> list[str]:
    avoid = list(risks)
    if best_window is None:
        avoid.append("Do not treat this location as a supported fishing forecast.")
        return avoid

    conditions = best_window.get("conditions") or {}
    wind = conditions.get("wind") or {}
    swell = conditions.get("swell") or {}
    if float(wind.get("speed_knots") or 0) >= 18:
        avoid.append("Avoid exposed options if wind strengthens.")
    if float(swell.get("height_m") or 0) >= 1.8:
        avoid.append("Avoid exposed rocks or beaches if swell is uncomfortable or unsafe.")
    return avoid


def _confidence_note(confidence: Mapping[str, Any], tide_verification: Mapping[str, Any]) -> str:
    label = confidence.get("label")
    tide_status = tide_verification.get("status")
    if tide_status == "model_estimated":
        if label == "low":
            return "Lower confidence: this is a searched-coordinate preview, and tide phase uses model sea-level data rather than a local tide station."
        return "Medium confidence with caution: tide phase uses model sea-level data, not a verified local tide station."
    if tide_status == "live_verified_remote_station":
        if label == "low":
            return "Lower confidence: this is a searched-coordinate preview, and real tide events came from a distant station."
        return "Medium confidence with caution: real tide events came from a distant station."
    if label == "low":
        return "Lower confidence: this is a searched-coordinate preview, so treat it as nearby guidance rather than a confirmed local spot."
    return "Medium confidence: use the plan as a structured preview, not a guaranteed catch prediction."


def _data_source_note(tide_verification: Mapping[str, Any]) -> str:
    status = tide_verification.get("status")
    if status == "live_verified":
        return "Tide data came from a verified live tide source."
    if status == "live_verified_remote_station":
        distance = tide_verification.get("station_distance_km")
        return f"Tide data came from a real but distant station ({distance} km away)."
    if status == "provided_events":
        return "Tide data came from supplied tide events."
    if status == "model_estimated":
        return "Tide data came from Open-Meteo model sea-level data, not a local station."
    return "Tide phase is based on coarse approximation."


def _iter_structure_facilities(payload: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    for key in ("structure_facilities", "facilities", "structures"):
        facilities = payload.get(key)
        if isinstance(facilities, list):
            for item in facilities:
                if isinstance(item, Mapping):
                    yield item


def _feature_key(facility: Mapping[str, Any]) -> str | None:
    raw_key = facility.get("type") or facility.get("key") or facility.get("kind")
    return str(raw_key).lower().replace(" ", "_") if raw_key else None


def _facility_status_is_confirmed(facility: Mapping[str, Any]) -> bool:
    status = str(facility.get("status") or facility.get("verification_status") or "confirmed").lower()
    return status in {"confirmed", "verified", "mapped"}


def _facility_is_public(facility: Mapping[str, Any]) -> bool:
    access = str(facility.get("access") or "").lower()
    key = _feature_key(facility) or ""
    if access in {"private", "no", "customers"}:
        return False
    if access in PUBLIC_ACCESS_VALUES:
        return True
    return key.startswith("public_")


def _confirmed_feature_keys(payload: Mapping[str, Any]) -> list[str]:
    confirmed: set[str] = set()
    for facility in _iter_structure_facilities(payload):
        if not _facility_status_is_confirmed(facility):
            continue
        key = _feature_key(facility)
        if key:
            confirmed.add(key)
    return sorted(confirmed)


def _confirmed_public_feature_keys(payload: Mapping[str, Any]) -> list[str]:
    confirmed: set[str] = set()
    for facility in _iter_structure_facilities(payload):
        if not _facility_status_is_confirmed(facility) or not _facility_is_public(facility):
            continue
        key = _feature_key(facility)
        if key:
            confirmed.add(key)
    return sorted(confirmed)


def _public_structure_labels(payload: Mapping[str, Any], keys: tuple[str, ...]) -> list[str]:
    wanted = set(keys)
    labels = []
    seen = set()
    for key in keys:
        for facility in _iter_structure_facilities(payload):
            if not _facility_status_is_confirmed(facility) or not _facility_is_public(facility):
                continue
            facility_key = _feature_key(facility)
            if facility_key not in wanted or facility_key != key:
                continue
            label = str(facility.get("label") or PUBLIC_STRUCTURE_LABELS.get(facility_key, facility_key.replace("_", " ")))
            if label not in seen:
                labels.append(label)
                seen.add(label)
    return labels


def _public_structure_action_labels(payload: Mapping[str, Any], keys: tuple[str, ...]) -> list[str]:
    public_keys = set(_confirmed_public_feature_keys(payload))
    labels = []
    for key in keys:
        if key not in public_keys:
            continue
        if key in {"public_jetty", "public_pier", "public_wharf"}:
            labels.append("a mapped public jetty")
        elif key == "fishing_platform":
            labels.append("a mapped public fishing platform")
        elif key == "rocky_shoreline":
            labels.append("a mapped rocky shoreline")
        else:
            labels.append(f"a mapped {key.replace('_', ' ')}")
    deduped = []
    for label in labels:
        if label not in deduped:
            deduped.append(label)
    return deduped


def _inferred_signal_keys(payload: Mapping[str, Any]) -> list[str]:
    best_window = (payload.get("hero") or {}).get("best_window") or {}
    signals: set[str] = set()
    for item in best_window.get("expanded_water_types") or []:
        if isinstance(item, Mapping) and item.get("key"):
            signals.add(str(item["key"]))
    for item in best_window.get("water_type_scores") or []:
        if isinstance(item, Mapping) and item.get("key"):
            signals.add(str(item["key"]))
    dominant = best_window.get("dominant_water_type")
    if dominant:
        signals.add(str(dominant))
    return sorted(signals)


def _terrain_certainty(payload: Mapping[str, Any]) -> dict[str, Any]:
    confirmed = _confirmed_feature_keys(payload)
    confirmed_public = _confirmed_public_feature_keys(payload)
    has_public_jetty = any(key in PUBLIC_JETTY_FEATURE_KEYS for key in confirmed_public)
    forbidden = set(UNCONFIRMED_STRUCTURE_TERMS)
    if has_public_jetty:
        forbidden -= UNCONFIRMED_PUBLIC_JETTY_TERMS
    return {
        "confirmed_features": confirmed,
        "confirmed_public_features": confirmed_public,
        "inferred_signals": _inferred_signal_keys(payload),
        "forbidden_claims": sorted(forbidden),
        "copy_rule": (
            "Only claim a public jetty, pier, or wharf when it is present in confirmed_features. "
            "Do not treat boat ramps as public jetties. "
            "Broad inferred water-type signals are allowed, but must stay cautious."
        ),
    }


def _apply_public_structure_guidance(payload: Mapping[str, Any], plan: dict[str, Any]) -> None:
    primary_labels = _public_structure_labels(payload, PRIMARY_PUBLIC_STRUCTURE_KEYS)
    primary_action_labels = _public_structure_action_labels(payload, PRIMARY_PUBLIC_STRUCTURE_KEYS)
    backup_labels = _public_structure_labels(payload, BACKUP_PUBLIC_STRUCTURE_KEYS)
    backup_action_labels = _public_structure_action_labels(payload, BACKUP_PUBLIC_STRUCTURE_KEYS)
    if primary_labels and plan.get("primary_action"):
        joined = " and ".join(primary_action_labels[:2] or ["a mapped public structure"])
        primary = dict(plan["primary_action"])
        time_hint = _representative_time_hint(primary.get("representative_time"))
        primary["text"] = (
            f"Start at {joined}{time_hint}. "
            "Fish the first 60-90 minutes hard; if there is no bait, current line, or visible activity, switch rather than waiting it out."
        )
        primary["confirmed_structure"] = primary_labels[:2]
        plan["primary_action"] = primary

    backup_unique = [label for label in backup_labels if label not in primary_labels[:2]]
    backup_action_unique = [
        label for label in backup_action_labels if label not in (primary_action_labels[:2] or [])
    ]
    if backup_unique:
        backup = dict(plan.get("backup_action") or {"water_type": None, "score": None})
        backup_label = backup_action_unique[0] if backup_action_unique else "another mapped public structure"
        backup["text"] = (
            f"Backup option: shift to {backup_label} if the first structure is crowded, closed, or lifeless."
        )
        backup["confirmed_structure"] = backup_unique[:1]
        plan["backup_action"] = backup


def _representative_time_hint(value: Any) -> str:
    if not isinstance(value, str) or "T" not in value:
        return ""
    time_part = value.split("T", 1)[1][:5]
    if len(time_part) != 5:
        return ""
    return f" around {time_part}; aim to arrive about 30 minutes before that"


def _contains_forbidden_claim(value: Any, forbidden_terms: set[str]) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in forbidden_terms)
    if isinstance(value, list):
        return any(_contains_forbidden_claim(item, forbidden_terms) for item in value)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim(item, forbidden_terms) for item in value.values())
    return False


def _assert_model_text_is_terrain_safe(model_text: Mapping[str, Any], terrain: Mapping[str, Any]) -> None:
    forbidden_terms = set(terrain.get("forbidden_claims") or [])
    allowed_text = {key: model_text[key] for key in MODEL_TEXT_FIELDS if key in model_text}
    if forbidden_terms and _contains_forbidden_claim(allowed_text, forbidden_terms):
        raise ValueError("GitHub Models planner text included an unconfirmed terrain claim.")


def _unsupported_plan(payload: Mapping[str, Any], source: str) -> dict[str, Any]:
    tide_verification = payload.get("tide_verification") or {}
    confidence = payload.get("confidence") or {"label": "unsupported"}
    plan = {
        "contract_version": PLAN_CONTRACT_VERSION,
        "source": source,
        "planner_provider": "rule_based",
        "recommendation": _recommendation(None, "unsupported"),
        "primary_action": {
            "text": "Search or move to a supported coastal or tidal fishing area before using this forecast.",
            "time_window": None,
            "water_type": None,
            "behavior_group": None,
            "score": None,
        },
        "backup_action": None,
        "avoid": ["Do not use this unsupported location as a fishing plan."],
        "risks": ["The selected location is outside the current coastal and tidal forecast scope."],
        "confidence_note": _confidence_note(confidence, tide_verification),
        "data_source_note": _data_source_note(tide_verification),
        "terrain_certainty": _terrain_certainty(payload),
        "safety_rules": {
            "score_modified": False,
            "best_window_modified": False,
            "support_status_modified": False,
            "terrain_claims_guarded": True,
        },
    }
    return plan


def _rule_based_plan(payload: Mapping[str, Any], *, source: str = "rule_based") -> dict[str, Any]:
    hero = payload.get("hero") or {}
    best_window = hero.get("best_window")
    if best_window is None:
        return _unsupported_plan(payload, source)

    confidence = payload.get("confidence") or {}
    tide_verification = payload.get("tide_verification") or {}
    explanation = payload.get("explanation") or {}
    risks = list(explanation.get("risks") or [])
    confidence_label = str(confidence.get("label", "low"))

    plan = {
        "contract_version": PLAN_CONTRACT_VERSION,
        "source": source,
        "planner_provider": "rule_based",
        "recommendation": _recommendation(hero.get("score"), confidence_label),
        "primary_action": _primary_action(best_window, confidence_label),
        "backup_action": _backup_action(explanation),
        "avoid": _avoid(best_window, risks),
        "risks": risks,
        "confidence_note": _confidence_note(confidence, tide_verification),
        "data_source_note": _data_source_note(tide_verification),
        "terrain_certainty": _terrain_certainty(payload),
        "safety_rules": {
            "score_modified": False,
            "best_window_modified": False,
            "support_status_modified": False,
            "terrain_claims_guarded": True,
        },
    }
    _apply_public_structure_guidance(payload, plan)
    return plan


def _whitelisted_model_input(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "hero": {
            "score": (payload.get("hero") or {}).get("score"),
            "best_window": (payload.get("hero") or {}).get("best_window"),
        },
        "confidence": payload.get("confidence"),
        "tide_verification": payload.get("tide_verification"),
        "explanation": payload.get("explanation"),
        "summary": {"best_windows": (payload.get("summary") or {}).get("best_windows")},
        "daily_forecast": [
            {"date": day.get("date"), "best_window": day.get("best_window")}
            for day in payload.get("daily_forecast", [])
            if isinstance(day, Mapping)
        ],
        "terrain_certainty": _terrain_certainty(payload),
    }


def _clean_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _clean_text_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return cleaned or None


def _merge_model_text(
    rule_plan: dict[str, Any],
    model_text: Mapping[str, Any],
    *,
    payload: Mapping[str, Any],
    terrain: Mapping[str, Any],
) -> dict[str, Any]:
    allowed = {key: model_text[key] for key in MODEL_TEXT_FIELDS if key in model_text}
    if not allowed:
        raise ValueError("GitHub Models planner response did not include allowed fields.")
    _assert_model_text_is_terrain_safe(model_text, terrain)

    merged = dict(rule_plan)
    merged["source"] = "github_models"
    merged["planner_provider"] = "github_models"
    recommendation_summary = _clean_text(allowed.get("recommendation_summary"))
    if recommendation_summary:
        merged["recommendation"] = dict(rule_plan["recommendation"])
        merged["recommendation"]["summary"] = recommendation_summary

    primary_action_text = _clean_text(allowed.get("primary_action_text"))
    if primary_action_text and merged.get("primary_action"):
        merged["primary_action"] = dict(rule_plan["primary_action"])
        merged["primary_action"]["text"] = primary_action_text

    backup_action_text = _clean_text(allowed.get("backup_action_text"))
    if backup_action_text and merged.get("backup_action"):
        merged["backup_action"] = dict(rule_plan["backup_action"])
        merged["backup_action"]["text"] = backup_action_text

    for list_key in ("avoid", "risks"):
        cleaned_list = _clean_text_list(allowed.get(list_key))
        if cleaned_list is not None:
            merged[list_key] = cleaned_list

    confidence_note = _clean_text(allowed.get("confidence_note"))
    if confidence_note:
        merged["confidence_note"] = confidence_note

    data_source_note = _clean_text(allowed.get("data_source_note"))
    if data_source_note:
        merged["data_source_note"] = data_source_note

    _preserve_required_cautions(rule_plan, merged)
    _apply_public_structure_guidance(payload, merged)
    return merged


def _preserve_required_cautions(rule_plan: Mapping[str, Any], merged: dict[str, Any]) -> None:
    """Do not let model wording weaken engine safety/source cautions."""
    critical_markers = ("model sea-level", "not a local", "distant station", "outside the current coastal")
    for note_key in ("confidence_note", "data_source_note"):
        rule_note = str(rule_plan.get(note_key) or "")
        merged_note = str(merged.get(note_key) or "")
        if any(marker in rule_note.lower() for marker in critical_markers):
            if not any(marker in merged_note.lower() for marker in critical_markers):
                merged[note_key] = rule_note

    for list_key in ("avoid", "risks"):
        existing = list(merged.get(list_key) or [])
        existing_lower = {str(item).lower() for item in existing}
        for required in rule_plan.get(list_key) or []:
            if str(required).lower() not in existing_lower:
                existing.append(required)
        merged[list_key] = existing


def build_fishing_plan(payload: Mapping[str, Any], *, planner_provider: str = "rule_based") -> dict[str, Any]:
    """Build a user action plan without changing forecast scores or status."""
    if planner_provider not in SUPPORTED_PLANNER_PROVIDERS:
        raise ValueError("planner_provider must be one of: rule_based, llm, github_models")

    if planner_provider == "rule_based":
        return _rule_based_plan(payload)

    rule_plan = _rule_based_plan(payload, source="rule_based_fallback")
    if planner_provider not in {"github_models", "llm"}:
        return rule_plan

    try:
        model_input = _whitelisted_model_input(payload)
        model_text = generate_github_models_plan_text(model_input)
        return _merge_model_text(rule_plan, model_text, payload=payload, terrain=model_input["terrain_certainty"])
    except (GitHubModelsError, OSError, TimeoutError, ValueError, KeyError, TypeError):
        return rule_plan
