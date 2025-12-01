from pathlib import Path
import tomllib


def get_api_key() -> str:
    """
    Read Census API key from config file at ~/.config/tablecensus/config.toml

    Expected config format:
    [census]
    api_key = "your_key_here"

    Returns:
        API key string if found, empty string otherwise
    """
    config_path = Path.home() / ".config" / "tablecensus" / "config.toml"

    if not config_path.exists():
        return ""

    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
            return config.get("census", {}).get("api_key", "")
    except Exception:
        # If there's any error reading the config, return empty string
        return ""
