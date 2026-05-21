import os
import sys
import warnings
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
        raw = config_path.read_bytes()
        # Strip UTF-8 BOM if present (common with PowerShell/Notepad on Windows)
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        config = tomllib.loads(raw.decode("utf-8"))
        return config.get("census", {}).get("api_key", "")
    except UnicodeDecodeError:
        warnings.warn(
            f"Config file {config_path} is not valid UTF-8. "
            "Re-save it as UTF-8 (PowerShell: Set-Content -Encoding utf8NoBOM)."
        )
        return ""
    except tomllib.TOMLDecodeError as e:
        warnings.warn(f"Config file {config_path} has invalid TOML: {e}")
        return ""
