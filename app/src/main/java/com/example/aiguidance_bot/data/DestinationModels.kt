package com.example.aiguidance_bot.data

data class DestinationCategory(
    val id: String,
    val name: String,
    val iconResId: Int
)

data class RecommendationItem(
    val id: String,
    val name: String,
    val location: String,
    val distanceMeters: Int,
    val imageUrl: String? = null,
    val description: String? = null
)

data class RoutePreviewResponse(
    val startLocation: String,
    val destination: String,
    val totalDistanceMeters: Int,
    val estimatedMinutes: Int,
    val instructions: List<String>
)
