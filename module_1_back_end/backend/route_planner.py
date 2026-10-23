"""
Route Planner Module
====================
Converts a destination into a sequence of DAMAN robot movement commands.

This module holds a simple mapping of known destinations to pre-defined routes.
Each route is a list of movement steps: { command, amount, speed (optional) }.

In a production system this would use pathfinding (A*, Dijkstra) on a building
map/graph, but for the workshop a lookup table is practical and safe.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Pre-defined routes from MAIN_ENTRANCE to known destinations
# ---------------------------------------------------------------------------
# Each route is a list of dicts with keys: command, amount
# command: forward | backward | left | right | stop
# amount:  cm (for forward/backward) or degrees (for left/right)
# ---------------------------------------------------------------------------
ROUTES: dict[str, list[dict]] = {
    "ROOM_105": [
        {"command": "forward",  "amount": 30},
        {"command": "left",     "amount": 90},
        {"command": "forward",  "amount": 20},
        {"command": "right",    "amount": 90},
        {"command": "forward",  "amount": 20},
        {"command": "stop",     "amount": 0},
    ],
    "LIBRARY": [
        {"command": "forward",  "amount": 50},
        {"command": "left",     "amount": 90},
        {"command": "forward",  "amount": 50},
        {"command": "stop",     "amount": 0},
    ],
    "CAFETERIA": [
        {"command": "forward",  "amount": 30},
        {"command": "right",    "amount": 90},
        {"command": "forward",  "amount": 40},
        {"command": "stop",     "amount": 0},
    ],
    "LECTURE_HALL_A": [
        {"command": "forward",  "amount": 50},
        {"command": "stop",     "amount": 0},
    ],
    "ADMIN_OFFICE": [
        {"command": "forward",  "amount": 20},
        {"command": "left",     "amount": 90},
        {"command": "forward",  "amount": 30},
        {"command": "left",     "amount": 90},
        {"command": "forward",  "amount": 10},
        {"command": "stop",     "amount": 0},
    ],
    "LAB_1": [
        {"command": "forward",  "amount": 40},
        {"command": "right",    "amount": 90},
        {"command": "forward",  "amount": 20},
        {"command": "stop",     "amount": 0},
    ],
    "PARKING": [
        {"command": "backward", "amount": 30},
        {"command": "right",    "amount": 90},
        {"command": "forward",  "amount": 50},
        {"command": "stop",     "amount": 0},
    ],
}

# Aliases — common ways users might say a destination name
DESTINATION_ALIASES: dict[str, str] = {
    "room 105":        "ROOM_105",
    "room105":         "ROOM_105",
    "library":         "LIBRARY",
    "the library":     "LIBRARY",
    "cafeteria":       "CAFETERIA",
    "canteen":         "CAFETERIA",
    "food court":      "CAFETERIA",
    "lecture hall a":   "LECTURE_HALL_A",
    "lecture hall":     "LECTURE_HALL_A",
    "hall a":          "LECTURE_HALL_A",
    "admin office":    "ADMIN_OFFICE",
    "admin":           "ADMIN_OFFICE",
    "administration":  "ADMIN_OFFICE",
    "lab 1":           "LAB_1",
    "laboratory 1":    "LAB_1",
    "lab1":            "LAB_1",
    "parking":         "PARKING",
    "parking lot":     "PARKING",
    "car park":        "PARKING",
}


def resolve_destination(raw_destination: Optional[str]) -> Optional[str]:
    """
    Resolve a free-form destination string to a canonical destination ID.

    Returns None if the destination cannot be resolved.
    """
    if not raw_destination:
        return None

    cleaned = raw_destination.strip().lower()

    # Try alias lookup first
    if cleaned in DESTINATION_ALIASES:
        return DESTINATION_ALIASES[cleaned]

    # Try uppercase exact match
    upper = cleaned.upper().replace(" ", "_")
    if upper in ROUTES:
        return upper

    return None


def get_route(destination_id: str) -> Optional[list[dict]]:
    """
    Return the pre-defined route for a given canonical destination ID.

    Returns None if no route exists.
    """
    return ROUTES.get(destination_id)


def get_route_for_destination(raw_destination: str) -> dict:
    """
    High-level function: resolve a destination name and return the route.

    Returns a dict with:
        - found: bool
        - destination_id: str or None
        - route: list of movement steps, or []
        - message: human-readable summary
    """
    dest_id = resolve_destination(raw_destination)

    if dest_id is None:
        return {
            "found": False,
            "destination_id": None,
            "route": [],
            "message": f"Sorry, I don't know how to get to '{raw_destination}'. "
                       f"Known destinations: {', '.join(sorted(ROUTES.keys()))}",
        }

    route = get_route(dest_id)
    if route is None:
        return {
            "found": False,
            "destination_id": dest_id,
            "route": [],
            "message": f"Destination '{dest_id}' recognised but no route is configured.",
        }

    # Build a human-readable summary of the route
    steps_desc = []
    for step in route:
        cmd = step["command"]
        amt = step["amount"]
        if cmd in ("forward", "backward"):
            steps_desc.append(f"{cmd.capitalize()} {amt} cm")
        elif cmd in ("left", "right"):
            steps_desc.append(f"Turn {cmd} {amt}°")
        elif cmd == "stop":
            steps_desc.append("Stop")
    route_summary = " → ".join(steps_desc)

    return {
        "found": True,
        "destination_id": dest_id,
        "route": route,
        "message": f"Route to {dest_id}: {route_summary}",
    }


def list_destinations() -> list[str]:
    """Return a sorted list of all known destination IDs."""
    return sorted(ROUTES.keys())
