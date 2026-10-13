package com.example.aiguidance_bot.data

import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
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
        "http://192.168.43.211:8000/api/v1/assistant/query"

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