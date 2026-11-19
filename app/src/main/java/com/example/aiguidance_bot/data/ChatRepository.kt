
package com.example.aiguidance_bot.data

import java.io.File

class ChatRepository(private val apiService: ApiService = ApiService()) {

    suspend fun getAiResponse(prompt: String): String {
        return apiService.sendMessage(prompt)
    }

    suspend fun sendVoiceAudio(audioFile: File): AssistantVoiceResponse {
        return apiService.sendVoiceFile(audioFile)
    }

    suspend fun searchDestinations(
        query: String,
        category: String?
    ): List<RecommendationItem> {

        val results = if (query.isBlank()) {
            FtmkLocationDatabase.rooms
        } else {
            FtmkLocationDatabase.rooms.filter { room ->
                room.nameMalay.contains(query, ignoreCase = true) ||
                        room.nameEnglish.contains(query, ignoreCase = true) ||
                        room.id.contains(query, ignoreCase = true) ||
                        room.block.contains(query, ignoreCase = true)
            }
        }

        val filteredResults = when (category) {
            null, "", "cat_all" -> results
            "cat_lib" -> results.filter {
                it.category.contains("Library", ignoreCase = true)
            }
            "cat_food" -> results.filter {
                it.category.contains("Food", ignoreCase = true)
            }
            "cat_class" -> results.filter {
                it.category.contains("Lecture", ignoreCase = true)
            }
            else -> results
        }

        return filteredResults.map { room ->
            RecommendationItem(
                id = room.id,
                name = room.nameEnglish,
                location = "${room.block}, Level ${room.level}",
                distanceMeters = 0,
                description = room.nameMalay
            )
        }
    }

    suspend fun getRoutePreview(
        startId: String,
        destId: String
    ): RoutePreviewResponse {

        val start = FtmkLocationDatabase.rooms.find {
            it.id == startId
        }

        val destination = FtmkLocationDatabase.rooms.find {
            it.id == destId
        }

        return RoutePreviewResponse(
            startLocation = start?.nameEnglish ?: startId,
            destination = destination?.nameEnglish ?: destId,
            totalDistanceMeters = 0,
            estimatedMinutes = 0,
            instructions = listOf(
                "Start from ${start?.nameEnglish ?: startId}",
                "Proceed to ${destination?.nameEnglish ?: destId}"
            )
        )
    }
}
