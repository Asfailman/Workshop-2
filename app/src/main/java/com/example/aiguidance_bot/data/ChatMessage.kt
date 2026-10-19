package com.example.aiguidance_bot.data

import java.util.UUID

enum class Sender {
    USER, AI
}

data class ChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val text: String,
    val sender: Sender,
    val timestamp: Long = System.currentTimeMillis()
)
