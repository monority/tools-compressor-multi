import yaml
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).parent.parent.parent / "config.default.yaml"

def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load YAML config with defaults."""
    config: dict[str, Any] = {}
    if DEFAULT_CONFIG.exists():
        config = yaml.safe_load(DEFAULT_CONFIG.read_text()) or {}
    if config_path and config_path.exists():
        user_cfg = yaml.safe_load(config_path.read_text()) or {}
        _deep_merge(config, user_cfg)
    return config

def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v

def get_preset(config: dict, fmt: str, quality: str) -> dict[str, Any]:
    """Get preset for format and quality level."""
    return config.get("presets", {}).get(fmt, {}).get(quality, {})
