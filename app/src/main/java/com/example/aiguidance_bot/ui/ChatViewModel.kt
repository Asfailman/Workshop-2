package com.example.aiguidance_bot.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aiguidance_bot.data.ChatMessage
import com.example.aiguidance_bot.data.ChatRepository
import com.example.aiguidance_bot.data.Sender
import kotlinx.coroutines.launch

class ChatViewModel(private val repository: ChatRepository = ChatRepository()) : ViewModel() {

    private val _messages = MutableLiveData<MutableList<ChatMessage>>(mutableListOf())
    val messages: LiveData<MutableList<ChatMessage>> get() = _messages

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> get() = _isLoading

    // Intents that should trigger robot navigation
    private val navigationIntents = setOf("GUIDANCE_REQUEST", "DESTINATION_RECOMMENDATION")

    init {
        val welcomeMsg = ChatMessage(
            text = "Hello Member 1! I am your AI Guidance Assistant for BAXU3923. Ask me anything about your project or tasks.",
            sender = Sender.AI
        )
        _messages.value?.add(welcomeMsg)
        _messages.value = _messages.value
    }

    fun sendMessage(text: String) {
        if (text.isBlank()) return

        val userMsg = ChatMessage(text = text, sender = Sender.USER)
        val currentList = _messages.value ?: mutableListOf()
        currentList.add(userMsg)
        _messages.value = currentList
        _isLoading.value = true

        viewModelScope.launch {
            val response = repository.getAiResponse(text)

            // Add the AI reply to chat
            val aiMsg = ChatMessage(text = response.reply, sender = Sender.AI)
            val updatedList = _messages.value ?: mutableListOf()
            updatedList.add(aiMsg)
            _messages.value = updatedList
            _isLoading.value = false

            // If AI detected a navigation intent with a route, trigger robot navigation
            val intent = response.intent ?: ""
            val navigation = response.navigation
            val destinationId = navigation?.destination_id

            if (intent in navigationIntents && navigation != null && navigation.available && destinationId != null) {
                triggerRobotNavigation(destinationId)
            }
        }
    }

    /**
     * Send robot navigation command to the backend.
     * The backend will forward movement commands to the DAMAN BridgeServer.
     */
    private fun triggerRobotNavigation(destination: String) {
        // Post a status message to chat
        addSystemMessage("🤖 Sending navigation commands to DAMAN robot...")

        viewModelScope.launch {
            val result = repository.navigateRobot(destination)

            val statusMsg = if (result.success) {
                "✅ Robot navigation complete! " +
                        "${result.commands_sent} commands sent to ${result.destination_id}."
            } else {
                "⚠️ Robot navigation issue: ${result.message ?: "Unknown error"}. " +
                        "Make sure the DAMAN robot BridgeServer is running."
            }

            addSystemMessage(statusMsg)
        }
    }

    private fun addSystemMessage(text: String) {
        val msg = ChatMessage(text = text, sender = Sender.AI)
        val list = _messages.value ?: mutableListOf()
        list.add(msg)
        _messages.value = list
    }
}

