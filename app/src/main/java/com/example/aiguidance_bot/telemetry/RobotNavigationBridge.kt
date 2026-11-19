package com.example.aiguidance_bot.telemetry

import android.util.Log
import android.webkit.JavascriptInterface
import org.json.JSONObject

/**
 * Robot Telemetry Dispatcher:
 * Parses waypoint vectors (distance, heading, floor transitions) and dispatches robot commands.
 */
class RobotNavigationBridge(
    private val onTelemetryReceived: (distanceMeters: Double, estimatedSeconds: Int, waypointsCount: Int) -> Unit
) {
    @JavascriptInterface
    fun onRouteCalculated(payloadJson: String) {
        try {
            val routeData = JSONObject(payloadJson)
            
            // Extract core navigation metrics for the HUD and Robot dispatch
            val distanceMeters = routeData.optDouble("total_distance_meters", 0.0)
            val estimatedSeconds = routeData.optInt("estimated_escort_seconds", 0)
            
            // Extract detailed robot vectors (segment_distance_m, heading_deg)
            val robotWaypoints = routeData.optJSONArray("robot_waypoints")
            val waypointsCount = robotWaypoints?.length() ?: 0

            Log.d("RobotNavBridge", "Dispatching Robot...")
            Log.d("RobotNavBridge", "Total Distance: ${distanceMeters}m")
            Log.d("RobotNavBridge", "ETA: ${estimatedSeconds}s")
            Log.d("RobotNavBridge", "Segments to navigate: $waypointsCount")

            // Send to UI HUD (or hardware ROS bridge in future)
            onTelemetryReceived(distanceMeters, estimatedSeconds, waypointsCount)

        } catch (exception: Exception) {
            Log.e("RobotNavBridge", "Failed to parse telemetry JSON", exception)
        }
    }
}