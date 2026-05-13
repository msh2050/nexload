"""Persistent settings for NexLoad (~/.local/share/nexload/settings.json)."""

import json
import os

_SETTINGS_FILE = os.path.expanduser("~/.local/share/nexload/settings.json")

DEFAULTS = {
    "downloader":   "auto",               # auto | aria2c | axel | builtin
    "connections":  16,                   # parallel connections per download
    "download_dir": os.path.expanduser("~/Downloads"),
    "max_retries":  8,                    # urllib fallback retries
}

_cache: dict | None = None


def load() -> dict:
    global _cache
    try:
        with open(_SETTINGS_FILE) as f:
            data = json.load(f)
        _cache = {**DEFAULTS, **data}
    except Exception:
        _cache = dict(DEFAULTS)
    return _cache


def save(data: dict) -> None:
    global _cache
    _cache = {**DEFAULTS, **data}
    os.makedirs(os.path.dirname(_SETTINGS_FILE), exist_ok=True)
    try:
        with open(_SETTINGS_FILE, "w") as f:
            json.dump(_cache, f, indent=2)
    except Exception:
        pass


def get(key: str, default=None):
    if _cache is None:
        load()
    return _cache.get(key, default if default is not None else DEFAULTS.get(key))


def all_settings() -> dict:
    if _cache is None:
        load()
    return dict(_cache)
