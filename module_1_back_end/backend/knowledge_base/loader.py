"""
Knowledge Base — Location Data Loader
=======================================
Loads destination data from locations.json and provides it to services.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

# Path to the locations data file
DATA_DIR = Path(__file__).parent / "data"
LOCATIONS_FILE = DATA_DIR / "locations.json"

# Module-level cache (loaded once, reused across requests)
_locations_cache: Optional[List[Dict]] = None


def load_locations() -> List[Dict]:
    """
    Read and parse locations.json from disk.
    Returns a list of location dictionaries.
    Caches the result after first load.
    """
    global _locations_cache

    if _locations_cache is not None:
        return _locations_cache

    if not LOCATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Locations data file not found: {LOCATIONS_FILE}. "
            f"Please ensure locations.json exists in knowledge_base/data/"
        )

    with open(LOCATIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Support both {"locations": [...]} and bare [...] formats
    if isinstance(data, dict):
        locations = data.get("locations", [])
    elif isinstance(data, list):
        locations = data
    else:
        raise ValueError("locations.json must contain a JSON object or array.")

    # Filter to only active destinations
    _locations_cache = [loc for loc in locations if loc.get("is_active", True)]
    return _locations_cache


def reload_locations() -> List[Dict]:
    """Force reload locations from disk (clears cache)."""
    global _locations_cache
    _locations_cache = None
    return load_locations()