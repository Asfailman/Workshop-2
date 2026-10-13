package com.example.aiguidance_bot.data

import android.util.Log
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
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    private val gson = Gson()

    var apiUrl: String = "https://api.openai.com/v1/chat/completions"
    var apiKey: String = ""

    suspend fun sendMessage(prompt: String): String = withContext(Dispatchers.IO) {
        if (apiKey.isBlank()) {
            delay(1000)
            return@withContext "AI Guidance Bot (Mock Response): I received your message: \"$prompt\". How can I help you further with your BAXU3923 project or guidance task?"
        }

        try {
            val jsonBody = mapOf(
                "model" to "gpt-3.5-turbo",
                "messages" to listOf(
                    mapOf("role" to "user", "content" to prompt)
                )
            )
            val bodyString = gson.toJson(jsonBody)
            val body = bodyString.toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(apiUrl)
                .addHeader("Authorization", "Bearer $apiKey")
                .addHeader("Content-Type", "application/json")
                .post(body)
                .build()

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    throw IOException("Unexpected response code: ${response.code}")
                }
                val responseBody = response.body?.string() ?: throw IOException("Empty response body")
                val chatResponse = gson.fromJson(responseBody, ChatCompletionResponse::class.java)
                return@withContext chatResponse.choices.firstOrNull()?.message?.content?.trim()
                    ?: "No response content from AI."
            }
        } catch (e: Exception) {
            Log.e("ApiService", "API error", e)
            "Error connecting to AI API: ${e.localizedMessage}. Please check your internet connection or API key."
        }
    }
}

data class ChatCompletionResponse(
    val choices: List<Choice>
)

data class Choice(
    val message: MessageContent
)

data class MessageContent(
    val content: String
)
