"""Minimal deterministic state reconstruction from a verified event history."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def reconstruct_state(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for event in events:
        if event["event_type"] == "state.set":
            payload = event["payload"]
            if not isinstance(payload, dict) or set(payload) != {"key", "value"}:
                raise ValueError("state.set payload must contain exactly key and value")
            if not isinstance(payload["key"], str) or not payload["key"]:
                raise ValueError("state.set key must be non-empty")
            state[payload["key"]] = payload["value"]
    return state

