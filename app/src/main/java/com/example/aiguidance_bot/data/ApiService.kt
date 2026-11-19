package com.example.aiguidance_bot.data

import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

class ApiService {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()

    private val apiUrl =
        "https://rinse-upstart-favorable.ngrok-free.dev/api/v1/assistant/query"

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

    suspend fun sendVoiceFile(audioFile: File): AssistantVoiceResponse =
        withContext(Dispatchers.IO) {
            try {
                val voiceUrl = apiUrl.replace("/assistant/query", "/assistant/chat/voice")
                val requestBody = MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart("session_id", "android_robot_session")
                    .addFormDataPart("current_location_id", "MAIN_ENTRANCE")
                    .addFormDataPart("language", "auto")
                    .addFormDataPart(
                        "file",
                        audioFile.name,
                        audioFile.asRequestBody("audio/wav".toMediaType())
                    )
                    .build()

                val request = Request.Builder()
                    .url(voiceUrl)
                    .addHeader("ngrok-skip-browser-warning", "true")
                    .post(requestBody)
                    .build()

                client.newCall(request).execute().use { response ->
                    val responseBody = response.body?.string()
                        ?: throw IOException("Empty response body from voice STT")
                    if (!response.isSuccessful) {
                        throw IOException("Backend voice error ${response.code}: $responseBody")
                    }
                    gson.fromJson(responseBody, AssistantVoiceResponse::class.java)
                }
            } catch (e: Exception) {
                AssistantVoiceResponse(
                    reply = "Voice recognition error: ${e.message}",
                    transcribed_text = ""
                )
            }
        }
}

data class AssistantVoiceResponse(
    val reply: String,
    val transcribed_text: String? = null,
    val destination_id: String? = null,
    val error: String? = null,
    val stt_engine: String? = null,
    val stt_duration_ms: Float? = null
)

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