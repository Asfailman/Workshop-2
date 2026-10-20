package com.example.aiguidance_bot.data

class ChatRepository(private val apiService: ApiService = ApiService()) {
    suspend fun getAiResponse(prompt: String): String {
        return apiService.sendMessage(prompt)
    }
}
