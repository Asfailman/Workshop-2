package com.example.aiguidance_bot.data

import java.io.File

class ChatRepository(private val apiService: ApiService = ApiService()) {
    suspend fun getAiResponse(prompt: String): String {
        return apiService.sendMessage(prompt)
    }

    suspend fun sendVoiceAudio(audioFile: File): AssistantVoiceResponse {
        return apiService.sendVoiceFile(audioFile)
    }
}
