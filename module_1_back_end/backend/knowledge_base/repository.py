"""
Knowledge Base — Repository
=============================
Provides search, filter, and lookup operations for location data.
"""

from typing import List, Optional, Dict
from backend.knowledge_base.loader import load_locations


class KnowledgeBaseRepository:
    """
    Repository layer for destination data loaded from locations.json.
    Provides methods to search by text query, filter by category/building,
    and retrieve by ID.
    """

    def __init__(self):
        self._locations = load_locations()

    def get_all(self) -> List[Dict]:
        """Return all active destinations."""
        return list(self._locations)

    def get(self, destination_id: str) -> Optional[Dict]:
        """Return a single destination by its ID, or None if not found."""
        for loc in self._locations:
            if loc["id"] == destination_id:
                return dict(loc)
        return None

    def search(self, query: str) -> List[Dict]:
        """
        Search destinations by name, aliases, description, or building.
        Returns a list of matching destinations.
        """
        if not query:
            return self.get_all()

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

            # Check building
            if query_lower in loc.get("building", "").lower():
                results.append(dict(loc))
                continue

            # Check category
            if query_lower in loc.get("category", "").lower():
                results.append(dict(loc))
                continue

            # Check keywords
            if any(query_lower in kw.lower() for kw in loc.get("keywords", [])):
                results.append(dict(loc))
                continue

        return results

    def search_by_name(self, name: str) -> Optional[Dict]:
        """
        Find a location by name or alias (case-insensitive).
        Returns the first match or None.
        """
        if not name:
            return None

        name_lower = name.lower().strip()

        for loc in self._locations:
            # Exact name match
            if name_lower == loc["name"].lower():
                return dict(loc)

            # Alias match
            for alias in loc.get("aliases", []):
                if name_lower == alias.lower():
                    return dict(loc)

        # Partial match fallback
        for loc in self._locations:
            if name_lower in loc["name"].lower():
                return dict(loc)
            for alias in loc.get("aliases", []):
                if name_lower in alias.lower():
                    return dict(loc)

        return None

    def filter_by_category(self, category: str) -> List[Dict]:
        """Return all destinations matching a given category."""
        if not category:
            return []
        category_lower = category.lower().strip()
        return [
            dict(loc) for loc in self._locations
            if loc.get("category", "").lower() == category_lower
        ]

    def filter_by_building(self, building: str) -> List[Dict]:
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
        from backend.knowledge_base.loader import reload_locations
        self._locations = reload_locations()