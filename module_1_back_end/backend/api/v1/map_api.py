import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.services.routing_service import RoutingService

router = APIRouter()

# Data paths
DATA_DIR = Path(__file__).resolve().parents[2] / "knowledge_base" / "data"
MAP_FILE = DATA_DIR / "campus_map.json"
COORDS_FILE = DATA_DIR / "campus_coordinates.json"
LOCATIONS_FILE = DATA_DIR / "locations.json"

routing_service = RoutingService()

def _load_json(file_path: Path) -> Any:
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@router.get("/data")
async def get_map_data():
    """
    Returns full campus map schema, nodes with coordinates, edges,
    building boundaries, and categorized facilities for the live map directory UI.
    """
    map_raw = _load_json(MAP_FILE)
    coords_raw = _load_json(COORDS_FILE)
    locs_raw = _load_json(LOCATIONS_FILE).get("locations", [])
    
    loc_by_id = {loc["id"]: loc for loc in locs_raw}

    nodes = []
    for node in map_raw.get("nodes", []):
        nid = node["id"]
        coord = coords_raw.get(nid, {"x": 500, "y": 500, "icon": "📍", "category": "corridor", "label": node["name"]})
        loc_meta = loc_by_id.get(nid, {})

        nodes.append({
            "id": nid,
            "name": node["name"],
            "building": node.get("building", "FTMK"),
            "floor": node.get("floor", 1),
            "x": coord.get("x", 500),
            "y": coord.get("y", 500),
            "icon": coord.get("icon", "📍"),
            "category": coord.get("category", loc_meta.get("category", "corridor")),
            "label": coord.get("label", node["name"]),
            "is_facility": nid in loc_by_id or coord.get("category") not in ["corridor", "stairs", "bridge"],
            "description": loc_meta.get("description", ""),
            "facilities": loc_meta.get("facilities", []),
            "opening_hours": loc_meta.get("opening_hours")
        })

    blocks = {
        "Block A": {
            "name": "Block A",
            "title": "Administration & Main Lobby",
            "color": "#6366f1",
            "badge": "Admin • Lobby • C-ACT",
            "x": 380, "y": 580, "width": 240, "height": 150
        },
        "Block B": {
            "name": "Block B",
            "title": "AI, Robotics & Programming",
            "color": "#0284c7",
            "badge": "AI Labs • Robotics • VIVA",
            "x": 120, "y": 340, "width": 230, "height": 260
        },
        "Block C": {
            "name": "Block C",
            "title": "Software Eng, Databases & Systems",
            "color": "#059669",
            "badge": "Software Eng • Databases • Systems",
            "x": 120, "y": 80, "width": 230, "height": 240
        },
        "Block D": {
            "name": "Block D",
            "title": "Multimedia, VR & Studios",
            "color": "#d97706",
            "badge": "Multimedia • VR • Mini Theatre",
            "x": 650, "y": 80, "width": 240, "height": 240
        },
        "Block E": {
            "name": "Block E",
            "title": "Networking, Cyber & Cloud",
            "color": "#8b5cf6",
            "badge": "CCNA • Cybersecurity • Cloud",
            "x": 650, "y": 340, "width": 240, "height": 250
        }
    }

    return {
        "status": "success",
        "floors": [1, 2, 3, 4],
        "blocks": blocks,
        "nodes": nodes,
        "edges": map_raw.get("edges", []),
        "total_nodes": len(nodes),
        "total_edges": len(map_raw.get("edges", []))
    }

@router.get("/route")
async def get_route(start_id: str = Query(..., description="Origin node ID"),
                    destination_id: str = Query(..., description="Destination node ID")):
    """
    Computes shortest Dijkstra path between two campus locations and formats
    Waze-style coordinates and turn-by-turn guidance for live animation.
    """
    result = routing_service.get_shortest_route(start_id, destination_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    coords_raw = _load_json(COORDS_FILE)
    map_raw = _load_json(MAP_FILE)
    node_map = {n["id"]: n for n in map_raw.get("nodes", [])}

    path_ids = result.get("path_ids", [])
    points = []
    floor_transitions = []
    current_floor = None

    for pid in path_ids:
        node = node_map.get(pid, {})
        coord = coords_raw.get(pid, {"x": 500, "y": 500, "icon": "📍", "label": node.get("name", pid)})
        flr = node.get("floor", 1)

        pt = {
            "id": pid,
            "name": node.get("name", pid),
            "building": node.get("building", "FTMK"),
            "floor": flr,
            "x": coord.get("x", 500),
            "y": coord.get("y", 500),
            "icon": coord.get("icon", "📍"),
            "category": coord.get("category", "corridor"),
            "label": coord.get("label", node.get("name", pid))
        }
        points.append(pt)

        if flr != current_floor:
            current_floor = flr
            floor_transitions.append({"floor": flr, "start_node": pid, "start_name": pt["label"]})

    dist = result.get("total_distance", 0)
    # Average walking speed indoor: 1.2 meters per second
    est_seconds = int(dist / 1.2) if dist > 0 else 0

    return {
        "status": "success",
        "start_id": start_id,
        "destination_id": destination_id,
        "start_name": result.get("start", start_id),
        "destination_name": result.get("destination", destination_id),
        "total_distance": dist,
        "estimated_seconds": est_seconds,
        "estimated_time_formatted": f"~{max(1, round(est_seconds / 60))} min walk",
        "path_ids": path_ids,
        "points": points,
        "floor_transitions": floor_transitions,
        "instructions": result.get("instructions", [])
    }
