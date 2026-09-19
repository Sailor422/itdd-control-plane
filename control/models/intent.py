"""Versioned durable intent model and validation."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class IntentValidationError(ValueError):
    """Raised when an intent does not satisfy the Stage C contract."""


INTENT_STATUSES = {"DRAFT", "APPROVED", "SUPERSEDED"}
REQUIRED_KEYS = {
    "intent_id",
    "version",
    "status",
    "created_at",
    "created_by",
    "project_id",
    "title",
    "purpose",
    "requirements",
    "constraints",
    "acceptance_summary",
    "source_event_id",
    "schema_version",
}
OPTIONAL_KEYS = {"approved_by", "approved_at", "approval_event_id"}


def _timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str):
        raise IntentValidationError(f"{field} must be ISO-8601")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise IntentValidationError(f"{field} must be ISO-8601") from exc


def validate_intent(intent: dict[str, Any]) -> None:
    if not isinstance(intent, dict):
        raise IntentValidationError("intent must be an object")
    missing = REQUIRED_KEYS - set(intent)
    if missing:
        raise IntentValidationError(f"missing required keys: {sorted(missing)}")
    unknown = set(intent) - REQUIRED_KEYS - OPTIONAL_KEYS
    if unknown:
        raise IntentValidationError(f"unknown keys: {sorted(unknown)}")
    if not isinstance(intent["intent_id"], str) or not re.fullmatch(r"I-[0-9]+", intent["intent_id"]):
        raise IntentValidationError("intent_id must use I-NNN identity")
    if not isinstance(intent["version"], int) or intent["version"] < 1:
        raise IntentValidationError("version must be a positive integer")
    if intent["status"] not in INTENT_STATUSES:
        raise IntentValidationError("unsupported intent status")
    _timestamp(intent["created_at"], "created_at")
    for field in ("created_by", "project_id", "title", "purpose", "acceptance_summary", "source_event_id"):
        if not isinstance(intent[field], str) or not intent[field].strip():
            raise IntentValidationError(f"{field} must be a non-empty string")
    if not isinstance(intent["constraints"], list) or not all(isinstance(item, str) for item in intent["constraints"]):
        raise IntentValidationError("constraints must be a list of strings")
    if not isinstance(intent["requirements"], list) or not intent["requirements"]:
        raise IntentValidationError("requirements must be a non-empty list")
    requirement_ids: set[str] = set()
    for requirement in intent["requirements"]:
        if not isinstance(requirement, dict) or set(requirement) != {"requirement_id", "text"}:
            raise IntentValidationError("each requirement must contain requirement_id and text")
        requirement_id = requirement["requirement_id"]
        if not isinstance(requirement_id, str) or not re.fullmatch(r"REQ-[0-9]+", requirement_id):
            raise IntentValidationError("requirement_id must use REQ-NNN identity")
        if requirement_id in requirement_ids:
            raise IntentValidationError(f"duplicate requirement_id: {requirement_id}")
        if not isinstance(requirement["text"], str) or not requirement["text"].strip():
            raise IntentValidationError("requirement text must be non-empty")
        requirement_ids.add(requirement_id)
    if intent["schema_version"] != 1:
        raise IntentValidationError("unsupported intent schema_version")
    for field in ("approved_by", "approval_event_id"):
        if field in intent and (not isinstance(intent[field], str) or not intent[field].strip()):
            raise IntentValidationError(f"{field} must be a non-empty string")
    if "approved_at" in intent:
        _timestamp(intent["approved_at"], "approved_at")
    if intent["status"] == "APPROVED" and not {"approved_by", "approved_at", "approval_event_id"} <= set(intent):
        raise IntentValidationError("approved intent must record approval actor, time, and event")

