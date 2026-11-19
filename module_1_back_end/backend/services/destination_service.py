"""
Destination Service
===================
Provides business logic for destination querying, filtering, and details.
Backed by the KnowledgeBaseRepository.
"""

from typing import List, Optional, Dict
from backend.knowledge_base.repository import KnowledgeBaseRepository


class DestinationService:
    """
    Service layer providing destination lookup and search functionality.
    """

    def __init__(self, repository: Optional[KnowledgeBaseRepository] = None):
        self.repository = repository or KnowledgeBaseRepository()

    def search(self, query: str = "") -> List[Dict]:
        """
        Search destinations matching a query string.
        Matches across name, aliases, description, building, category, and keywords.
        If query is empty, returns all active destinations.
        """
        return self.repository.search(query)

    def get_by_id(self, destination_id: str) -> Optional[Dict]:
        """Retrieve a specific destination by its unique ID."""
        return self.repository.get(destination_id)

    def get_all(self) -> List[Dict]:
        """Retrieve all active destinations."""
        return self.repository.get_all()

    def search_by_name(self, name: str) -> Optional[Dict]:
        """Find a destination matching a name or alias."""
        return self.repository.search_by_name(name)

    def filter_by_category(self, category: str) -> List[Dict]:
        """Filter destinations by category."""
        return self.repository.filter_by_category(category)

    def filter_by_building(self, building: str) -> List[Dict]:
        """Filter destinations by building name."""
        return self.repository.filter_by_building(building)