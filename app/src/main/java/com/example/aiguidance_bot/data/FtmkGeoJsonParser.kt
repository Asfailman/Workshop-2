package com.example.aiguidance_bot.data

import android.content.Context
import org.json.JSONObject
import java.io.InputStreamReader

data class GeoJsonRoom(
    val id: String,
    val name: String,
    val level: Int
)

/**
 * Native Kotlin GeoJSON Helper:
 * Parses assets/ftmk_map.geojson on Android for offline native room search
 * and voice-command lookup across all rooms and floors.
 */
class FtmkGeoJsonParser(private val context: Context) {
    private val rooms = mutableListOf<GeoJsonRoom>()

    init {
        loadGeoJson()
    }

    private fun loadGeoJson() {
        try {
            val jsonStr = context.assets.open("ftmk_map.geojson").use { stream ->
                InputStreamReader(stream).readText()
            }
            val root = JSONObject(jsonStr)
            val features = root.getJSONArray("features")
            
            for (i in 0 until features.length()) {
                val feature = features.getJSONObject(i)
                val properties = feature.getJSONObject("properties")
                
                val id = properties.optString("id", "")
                val name = properties.optString("name", "")
                val level = properties.optInt("level", 1)
                
                if (id.isNotEmpty() && name.isNotEmpty()) {
                    rooms.add(GeoJsonRoom(id, name, level))
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    /**
     * Search function for the voice command or search bar.
     */
    fun searchRooms(query: String): List<GeoJsonRoom> {
        if (query.isBlank()) return emptyList()
        return rooms.filter { it.name.contains(query, ignoreCase = true) }
    }
}