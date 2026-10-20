package com.example.aiguidance_bot.data

import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

class ApiService {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()

    private val apiUrl =
        "https://dazzling-endurance-huddle.ngrok-free.dev/api/v1/assistant/query"

    // Module 2 Endpoints
    var campusApiUrl: String = "http://10.0.2.2:8000" // Replace with actual FastAPI URL

    suspend fun searchDestinations(query: String, category: String?): List<RecommendationItem> = withContext(Dispatchers.IO) {
        // Mock Implementation for Module 2 UI testing
        delay(1000)
        return@withContext listOf(
            RecommendationItem("1", "Main Library", "Building B, Level 1", 120, description = "Quiet study area and printing facilities."),
            RecommendationItem("2", "FTMK Block A", "Block A, Level 2", 250, description = "Computer science labs and lecture halls."),
            RecommendationItem("3", "Cafeteria Utama", "Student Center, Ground Floor", 80, description = "Food and beverages.")
        ).filter { 
            (query.isBlank() || it.name.contains(query, ignoreCase = true)) &&
            (category == null || category == "All" || it.description?.contains(category, ignoreCase = true) == true)
        }
    }

    suspend fun getRoutePreview(startId: String, destId: String): RoutePreviewResponse = withContext(Dispatchers.IO) {
        // Mock Implementation for Module 2 UI testing
        delay(800)
        RoutePreviewResponse(
            startLocation = "Main Entrance",
            destination = "Main Library",
            totalDistanceMeters = 120,
            estimatedMinutes = 3,
            instructions = listOf(
                "Walk straight for 50 meters.",
                "Turn right at the junction.",
                "Arrive at Building B, Level 1."
            )
        )
    }

    suspend fun sendMessage(prompt: String): String =
        withContext(Dispatchers.IO) {
            try {
                val requestData = AssistantQueryRequest(
                    session_id = "android_session",
                    message = prompt,
                    current_location_id = "MAIN_ENTRANCE"
                )

                val jsonBody = gson.toJson(requestData)
                val body = jsonBody.toRequestBody(
                    "application/json; charset=utf-8".toMediaType()
                )

                val request = Request.Builder()
                    .url(apiUrl)
                    .addHeader("ngrok-skip-browser-warning", "true")
                    .post(body)
                    .build()

                client.newCall(request).execute().use { response ->
                    val responseBody = response.body?.string()
                        ?: throw IOException("Empty response body")

                    if (!response.isSuccessful) {
                        throw IOException(
                            "Backend returned HTTP ${response.code}: $responseBody"
                        )
                    }

                    val result = gson.fromJson(
                        responseBody,
                        AssistantQueryResponse::class.java
                    )

                    result.reply
                }
            } catch (e: Exception) {
                "Unable to connect to the guidance backend: " +
                    (e.message ?: "Unknown error")
            }
        }
}

data class AssistantQueryRequest(
    val session_id: String,
    val message: String,
    val current_location_id: String
)

data class AssistantQueryResponse(
    val reply: String,
    val intent: String? = null,
    val destination_id: String? = null,
    val confidence: Double? = null,
    val session_id: String? = null,
    val error: String? = null
)
