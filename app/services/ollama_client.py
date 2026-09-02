"""Thin HTTP client for local Ollama model list/pull operations."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from app.config.settings import get_settings


def ollama_base_url() -> str:
    return get_settings().ollama_base_url.rstrip("/")


def list_installed_models(timeout: float = 5) -> set[str]:
    request = urllib.request.Request(f"{ollama_base_url()}/api/tags")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)

    names: set[str] = set()
    for model in payload.get("models", []):
        name = model.get("name")
        if not name:
            continue
        names.add(name)
        if ":" in name:
            names.add(name.split(":", 1)[0])
    return names


def installed_model_details(timeout: float = 5) -> list[dict[str, Any]]:
    request = urllib.request.Request(f"{ollama_base_url()}/api/tags")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    return list(payload.get("models", []))


def model_installed(model: str, installed: set[str] | None = None) -> bool:
    names = installed if installed is not None else list_installed_models()
    if model in names:
        return True
    base = model.split(":", 1)[0]
    return any(name == model or name.startswith(f"{base}:") for name in names)


def pull_model(
    model: str,
    *,
    on_status: Callable[[str], None] | None = None,
    timeout: float = 3600,
) -> None:
    body = json.dumps({"name": model, "stream": True}).encode("utf-8")
    request = urllib.request.Request(
        f"{ollama_base_url()}/api/pull",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while True:
            line = response.readline()
            if not line:
                break
            status = json.loads(line.decode("utf-8")).get("status")
            if status and on_status is not None:
                on_status(status)


def ollama_reachable(timeout: float = 2) -> bool:
    try:
        list_installed_models(timeout=timeout)
        return True
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False


__all__ = [
    "installed_model_details",
    "list_installed_models",
    "model_installed",
    "ollama_base_url",
    "ollama_reachable",
    "pull_model",
]
