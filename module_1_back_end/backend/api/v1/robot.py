"""
DAMAN Robot Control API
=======================
FastAPI endpoints for controlling the physical DAMAN robot.

Provides:
- POST /robot/move       — Send a single movement command to the robot
- POST /robot/route      — Execute a full route (list of commands) on the robot
- POST /robot/stop       — Emergency stop
- GET  /robot/status     — Check if the robot BridgeServer is reachable
- GET  /robot/destinations — List available destinations with routes
"""

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ...route_planner import (
    get_route_for_destination,
    list_destinations,
)

router = APIRouter()

# ---------------------------------------------------------------------------
# Configuration — CHANGE THIS to your DAMAN robot/bridge IP
# ---------------------------------------------------------------------------
ROBOT_BRIDGE_URL = "http://192.168.1.50:8088"


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class MoveCommand(BaseModel):
    command: str = Field(..., description="Movement command: forward, backward, left, right, stop")
    amount: int = Field(0, description="Distance in cm (forward/backward) or degrees (left/right)")
    speed: int = Field(200, description="Motor speed (1–600)")


class RouteRequest(BaseModel):
    destination: str = Field(..., description="Destination name or ID")


class NavigateRequest(BaseModel):
    destination: str = Field(..., description="Destination name from AI intent")
    session_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper: send a single command to the DAMAN BridgeServer
# ---------------------------------------------------------------------------
def _send_to_robot(command: str, amount: int = 0, speed: int = 200) -> dict:
    """Send a movement command to the DAMAN robot BridgeServer."""
    # Apply safety limits matching DamanRobotController.kt
    if command in ("forward", "backward"):
        amount = max(2, min(amount, 50))
    elif command in ("left", "right"):
        amount = max(1, min(amount, 90))
    else:
        amount = 0

    speed = max(1, min(speed, 600))

    payload = {
        "command": command,
        "amount": amount,
        "speed": speed,
    }

    try:
        resp = requests.post(
            f"{ROBOT_BRIDGE_URL}/manual/base",
            json=payload,
            timeout=5,
        )
        resp.raise_for_status()
        return {"success": True, "robot_response": resp.json()}
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach DAMAN robot BridgeServer. "
                   f"Is it running at {ROBOT_BRIDGE_URL}?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="DAMAN robot did not respond in time."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Robot command failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/move")
async def move_robot(cmd: MoveCommand):
    """Send a single movement command to the DAMAN robot."""
    result = _send_to_robot(cmd.command, cmd.amount, cmd.speed)
    return {
        "success": True,
        "command_sent": cmd.command,
        "amount": cmd.amount,
        "speed": cmd.speed,
        **result,
    }


@router.post("/navigate")
async def navigate_to_destination(req: NavigateRequest):
    """
    Navigate the robot to a named destination.

    Resolves the destination name, retrieves the route, and sends
    all movement commands to the robot sequentially.
    """
    route_info = get_route_for_destination(req.destination)

    if not route_info["found"]:
        return {
            "success": False,
            "message": route_info["message"],
            "destination_id": None,
            "route": [],
            "commands_sent": 0,
        }

    # Execute each movement step
    results = []
    for i, step in enumerate(route_info["route"]):
        try:
            result = _send_to_robot(
                command=step["command"],
                amount=step.get("amount", 0),
                speed=step.get("speed", 200),
            )
            results.append({
                "step": i + 1,
                "command": step["command"],
                "amount": step.get("amount", 0),
                "success": True,
            })
        except HTTPException as e:
            results.append({
                "step": i + 1,
                "command": step["command"],
                "amount": step.get("amount", 0),
                "success": False,
                "error": e.detail,
            })
            # Stop sending further commands on failure
            break

    all_success = all(r["success"] for r in results)

    return {
        "success": all_success,
        "destination_id": route_info["destination_id"],
        "message": route_info["message"],
        "route": route_info["route"],
        "commands_sent": len(results),
        "results": results,
    }


@router.post("/stop")
async def emergency_stop():
    """Send an emergency stop command to the DAMAN robot."""
    result = _send_to_robot("stop", 0, 200)
    return {"success": True, "message": "Emergency stop sent", **result}


@router.get("/status")
async def robot_status():
    """Check if the DAMAN robot BridgeServer is reachable."""
    try:
        resp = requests.get(
            f"{ROBOT_BRIDGE_URL}/manual/base",
            timeout=3,
        )
        return {
            "reachable": True,
            "bridge_url": ROBOT_BRIDGE_URL,
            "http_status": resp.status_code,
        }
    except Exception as e:
        return {
            "reachable": False,
            "bridge_url": ROBOT_BRIDGE_URL,
            "error": str(e),
        }


@router.get("/destinations")
async def available_destinations():
    """List all destinations the robot can navigate to."""
    destinations = list_destinations()
    return {
        "count": len(destinations),
        "destinations": destinations,
    }
