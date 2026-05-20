import os
import sys
from pathlib import Path
import tomllib


def _config_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "tablecensus" / "config.toml"
    return Path.home() / ".config" / "tablecensus" / "config.toml"


def get_api_key() -> str:
    config_path = _config_path()

    if not config_path.exists():
        return ""

    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
            return config.get("census", {}).get("api_key", "")
    except Exception:
        return ""
