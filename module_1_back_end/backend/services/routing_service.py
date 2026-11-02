import json
import heapq
from pathlib import Path
from typing import Dict, Any

# Locate the campus_map.json file relative to this service file
MAP_FILE = Path(__file__).parent.parent / "knowledge_base" / "data" / "campus_map.json"

class RoutingService:
    def __init__(self):
        self.nodes: Dict[str, dict] = {}
        self.graph: Dict[str, list] = {}
        self.load_map()

    def load_map(self):
        """Loads the JSON map and builds an adjacency list graph."""
        if not MAP_FILE.exists():
            raise FileNotFoundError(f"Map file not found at {MAP_FILE}")
            
        with open(MAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 1. Map IDs to full node data (name, building, floor)
        for node in data.get("nodes", []):
            self.nodes[node["id"]] = node
            self.graph[node["id"]] = []

        # 2. Build adjacency list
        for edge in data.get("edges", []):
            src = edge["source"]
            tgt = edge["target"]
            dist = edge.get("distance", 1)
            inst = edge.get("instruction", "Proceed.")
            
            # Add forward edge
            self.graph[src].append((tgt, dist, inst))
            # Add reverse edge (assuming two-way walking paths)
            self.graph[tgt].append((src, dist, inst))

    def get_shortest_route(self, start_id: str, destination_id: str) -> dict:
        """
        Runs Dijkstra's algorithm to find the shortest path.
        Returns a dictionary with the route instructions or an error.
        """
        if start_id not in self.graph or destination_id not in self.graph:
            return {"error": f"Invalid location ID. Check that '{start_id}' and '{destination_id}' exist in campus_map.json"}

        if start_id == destination_id:
            return {"error": "Start and destination cannot be the same."}

        # Priority Queue: (total_distance, current_node, path_taken)
        queue = [(0, start_id, [])]
        visited = set()
        min_distances = {start_id: 0}

        while queue:
            current_dist, current_node, path = heapq.heappop(queue)

            if current_node in visited:
                continue
            visited.add(current_node)
            
            # Append current node to the path history
            path = path + [current_node]

            # If we reached the destination, build the response
            if current_node == destination_id:
                return self._build_route_response(path, current_dist)

            # Check neighbors
            for neighbor, weight, _ in self.graph[current_node]:
                if neighbor not in visited:
                    new_dist = current_dist + weight
                    if new_dist < min_distances.get(neighbor, float('inf')):
                        min_distances[neighbor] = new_dist
                        heapq.heappush(queue, (new_dist, neighbor, path))

        return {"error": "No valid path found (disconnected route)."}

    def _build_route_response(self, path: list, total_distance: int) -> dict:
        """Translates the node path into human-readable instructions."""
        instructions = []
        
        # Loop through the path to extract the specific instructions for each edge
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            
            # Find the edge connecting u to v
            for neighbor, weight, inst in self.graph[u]:
                if neighbor == v:
                    instructions.append(inst)
                    break
                    
        return {
            "status": "success",
            "start": self.nodes[path[0]]["name"],
            "destination": self.nodes[path[-1]]["name"],
            "total_distance": total_distance,
            "path_ids": path,
            "instructions": instructions
        }