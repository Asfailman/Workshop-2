
package com.example.aiguidance_bot.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aiguidance_bot.data.ChatMessage
import com.example.aiguidance_bot.data.ChatRepository
import com.example.aiguidance_bot.data.FtmkLocationDatabase
import com.example.aiguidance_bot.data.Sender
import kotlinx.coroutines.launch
import java.io.File

class ChatViewModel(
    private val repository: ChatRepository = ChatRepository()
) : ViewModel() {

    private val _messages =
        MutableLiveData<MutableList<ChatMessage>>(mutableListOf())

    val messages: LiveData<MutableList<ChatMessage>> get() = _messages

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> get() = _isLoading

    init {
        val welcomeMsg = ChatMessage(
            text = "Hello Member 1! I am your AI Guidance Assistant for BAXU3923. Ask me anything about your project or tasks.",
            sender = Sender.AI
        )
        _messages.value?.add(welcomeMsg)
        _messages.value = _messages.value
    }

    private fun createAiMessage(
        userQuery: String,
        reply: String
    ): ChatMessage {

        val room = FtmkLocationDatabase.findRoomByQuery(userQuery)
            ?: FtmkLocationDatabase.findRoomByQuery(reply)

        return ChatMessage(
            text = reply,
            sender = Sender.AI,
            roomId = room?.id,
            roomName = room?.nameMalay,
            roomLevel = room?.level,
            roomBlock = room?.block
        )
    }

    fun sendMessage(text: String) {
        if (text.isBlank()) return

        val currentList = _messages.value ?: mutableListOf()
        currentList.add(ChatMessage(text = text, sender = Sender.USER))
        _messages.value = currentList
        _isLoading.value = true

        viewModelScope.launch {
            try {
                val aiReplyText = repository.getAiResponse(text)
                val aiMsg = createAiMessage(text, aiReplyText)

                val updatedList = _messages.value ?: mutableListOf()
                updatedList.add(aiMsg)
                _messages.value = updatedList
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun sendVoiceAudio(audioFile: File) {
        _isLoading.value = true

        viewModelScope.launch {
            try {
                val response = repository.sendVoiceAudio(audioFile)

                val userText = response.transcribed_text
                    ?.takeIf { it.isNotBlank() }
                    ?: "🎤 [Voice Query]"

                val userMsg = ChatMessage(
                    text = userText,
                    sender = Sender.USER
                )

                val aiMsg = createAiMessage(userText, response.reply)

                val updatedList = _messages.value ?: mutableListOf()
                updatedList.add(userMsg)
                updatedList.add(aiMsg)
                _messages.value = updatedList
            } finally {
                _isLoading.value = false
            }
        }
    }
}
