"""Deterministic Stage B event format and validation."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any


class EventValidationError(ValueError):
    """Raised when an event does not satisfy the Stage B contract."""


REQUIRED_KEYS = {
    "event_id",
    "event_type",
    "timestamp",
    "project_id",
    "actor_type",
    "actor_id",
    "previous_event_id",
    "payload",
    "schema_version",
    "event_hash",
    "previous_event_hash",
}
OPTIONAL_BINDINGS = {"intent_version", "graph_version", "execution_id", "git_sha"}
EVENT_TYPES = re.compile(r"^[a-z][a-z0-9_.-]*$")


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hashable_event(event: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(event)
    result.pop("event_hash", None)
    return result


def event_hash(event: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(_hashable_event(event)).encode("utf-8")).hexdigest()


def make_event(
    *,
    event_id: str,
    event_type: str,
    timestamp: str,
    project_id: str,
    actor_type: str,
    actor_id: str,
    previous_event_id: str | None,
    previous_event_hash: str | None,
    payload: Any,
    schema_version: int = 1,
    **bindings: str,
) -> dict[str, Any]:
    """Create a fully hashed event; optional bindings are included only when supplied."""

    event: dict[str, Any] = {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "project_id": project_id,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "previous_event_id": previous_event_id,
        "previous_event_hash": previous_event_hash,
        "payload": payload,
        "schema_version": schema_version,
    }
    event.update({key: value for key, value in bindings.items() if value is not None})
    event["event_hash"] = event_hash(event)
    return event


def validate_event(event: Mapping[str, Any], *, verify_hash: bool = True) -> None:
    if not isinstance(event, Mapping):
        raise EventValidationError("event must be an object")
    missing = REQUIRED_KEYS - set(event)
    if missing:
        raise EventValidationError(f"missing required keys: {sorted(missing)}")
    unknown = set(event) - REQUIRED_KEYS - OPTIONAL_BINDINGS
    if unknown:
        raise EventValidationError(f"unknown keys: {sorted(unknown)}")
    for key in ("event_id", "project_id", "actor_type", "actor_id"):
        if not isinstance(event[key], str) or not event[key].strip():
            raise EventValidationError(f"{key} must be a non-empty string")
    if not isinstance(event["event_type"], str) or not EVENT_TYPES.fullmatch(event["event_type"]):
        raise EventValidationError("event_type has invalid format")
    if event["schema_version"] != 1:
        raise EventValidationError("unsupported schema_version")
    if event["previous_event_id"] is not None and not isinstance(event["previous_event_id"], str):
        raise EventValidationError("previous_event_id must be a string or null")
    if event["previous_event_hash"] is not None and not isinstance(event["previous_event_hash"], str):
        raise EventValidationError("previous_event_hash must be a string or null")
    if not isinstance(event["payload"], (dict, list, str, int, float, bool, type(None))):
        raise EventValidationError("payload must be JSON-compatible")
    try:
        datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise EventValidationError("timestamp must be ISO-8601") from exc
    if not isinstance(event["event_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", event["event_hash"]):
        raise EventValidationError("event_hash must be a SHA-256 hex digest")
    if event["previous_event_hash"] is not None and not re.fullmatch(
        r"[0-9a-f]{64}", event["previous_event_hash"]
    ):
        raise EventValidationError("previous_event_hash must be a SHA-256 hex digest or null")
    if verify_hash and event_hash(event) != event["event_hash"]:
        raise EventValidationError("event_hash does not match event contents")

