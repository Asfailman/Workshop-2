package com.example.aiguidance_bot.data

class ChatRepository(private val apiService: ApiService = ApiService()) {
    suspend fun getAiResponse(prompt: String): AssistantQueryResponse {
        return apiService.sendMessage(prompt)
    }

    suspend fun navigateRobot(destination: String): RobotNavigateResponse {
        return apiService.navigateRobot(destination)
    }
}

