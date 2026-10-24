"""
Knowledge Base — Location Data Loader & Repository
===================================================
Loads destination data from locations.json and provides search,
filter, and lookup operations.

Part of Module 2 (AI Recommendation) — Member 2's territory.
"""

import json
import os
from typing import Optional


# Path to the locations data file
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_LOCATIONS_FILE = os.path.join(_DATA_DIR, "locations.json")

# Module-level cache (loaded once, reused across requests)
_locations_cache: Optional[list[dict]] = None


def _load_from_disk() -> list[dict]:
    """Read and parse locations.json from disk."""
    if not os.path.exists(_LOCATIONS_FILE):
        raise FileNotFoundError(
            f"Locations data file not found: {_LOCATIONS_FILE}. "
            f"Please ensure locations.json exists in AI/recommendation/data/"
        )

    with open(_LOCATIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("locations.json must contain a JSON array of destinations.")

    # Filter to only active destinations
    return [loc for loc in data if loc.get("is_active", True)]


class KnowledgeBase:
    """
    Repository layer for destination data. Provides methods to search
    by text query, filter by category/building, and retrieve by ID.
    """

    def __init__(self, locations_file: Optional[str] = None):
        """
        Args:
            locations_file: Optional path to a custom locations JSON file.
                            Defaults to AI/recommendation/data/locations.json.
        """
        global _locations_cache

        if locations_file:
            with open(locations_file, "r", encoding="utf-8") as f:
                self._locations = json.load(f)
        elif _locations_cache is not None:
            self._locations = _locations_cache
        else:
            _locations_cache = _load_from_disk()
            self._locations = _locations_cache

    def get_all(self) -> list[dict]:
        """Return all active destinations."""
        return list(self._locations)

    def get(self, destination_id: str) -> Optional[dict]:
        """
        Return a single destination by its ID, or None if not found.

        Args:
            destination_id: The unique destination ID (e.g., "DEST_001").
        """
        for loc in self._locations:
            if loc["id"] == destination_id:
                return dict(loc)
        return None

    def search(self, query: str) -> list[dict]:
        """
        Simple text search across destination name, aliases, and description.

        Args:
            query: Free-text search query.

        Returns:
            List of matching destinations.
        """
        if not query:
            return []

        query_lower = query.lower().strip()
        results = []

        for loc in self._locations:
            # Check name
            if query_lower in loc["name"].lower():
                results.append(dict(loc))
                continue

            # Check aliases
            if any(query_lower in alias.lower() for alias in loc.get("aliases", [])):
                results.append(dict(loc))
                continue

            # Check description
            if query_lower in loc.get("description", "").lower():
                results.append(dict(loc))
                continue

            # Check room number
            room = loc.get("room_number", "") or ""
            if query_lower in room.lower():
                results.append(dict(loc))
                continue

        return results

    def filter_by_category(self, category: str) -> list[dict]:
        """Return all destinations matching a given category."""
        if not category:
            return []
        category_lower = category.lower().strip()
        return [
            dict(loc) for loc in self._locations
            if loc.get("category", "").lower() == category_lower
        ]

    def filter_by_building(self, building: str) -> list[dict]:
        """Return all destinations in a specific building."""
        if not building:
            return []
        building_lower = building.lower().strip()
        return [
            dict(loc) for loc in self._locations
            if loc.get("building", "").lower() == building_lower
        ]

    def reload(self):
        """Reload the knowledge base from disk."""
        global _locations_cache
        _locations_cache = _load_from_disk()
        self._locations = _locations_cache
