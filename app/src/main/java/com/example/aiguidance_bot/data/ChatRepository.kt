package com.example.aiguidance_bot.data

class ChatRepository(private val apiService: ApiService = ApiService()) {
    suspend fun getAiResponse(prompt: String): String {
        return apiService.sendMessage(prompt)
    }

    suspend fun searchDestinations(query: String, category: String?): List<RecommendationItem> {
        return apiService.searchDestinations(query, category)
    }

    suspend fun getRoutePreview(startId: String, destId: String): RoutePreviewResponse {
        return apiService.getRoutePreview(startId, destId)
    }
}
