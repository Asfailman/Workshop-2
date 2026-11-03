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

class ChatViewModel(private val repository: ChatRepository = ChatRepository()) : ViewModel() {

    private val _messages = MutableLiveData<MutableList<ChatMessage>>(mutableListOf())
    val messages: LiveData<MutableList<ChatMessage>> get() = _messages

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> get() = _isLoading

    init {
        clearChat()
    }

    fun clearChat() {
        val welcomeMsg = ChatMessage(
            text = "Hello Member 1! I am your AI Guidance Assistant for BAXU3923. Ask me about any room or location in FTMK!",
            sender = Sender.AI
        )
        _messages.value = mutableListOf(welcomeMsg)
    }

    fun sendMessage(text: String) {
        if (text.isBlank()) return

        val userMsg = ChatMessage(text = text, sender = Sender.USER)
        val currentList = _messages.value ?: mutableListOf()
        currentList.add(userMsg)
        _messages.value = currentList
        _isLoading.value = true

        viewModelScope.launch {
            val aiReplyText = repository.getAiResponse(text)
            
            // Check if user query matches any FTMK Room
            val matchedRoom = FtmkLocationDatabase.findRoomByQuery(text) 
                ?: FtmkLocationDatabase.findRoomByQuery(aiReplyText)

            val aiMsg = if (matchedRoom != null) {
                val locationInfo = "\n\n📍 FTMK Location Found:\n• Room: ${matchedRoom.nameMalay} (${matchedRoom.nameEnglish})\n• Floor: Level ${matchedRoom.level} (Aras ${matchedRoom.level})\n• Block: ${matchedRoom.block}"
                ChatMessage(
                    text = aiReplyText + locationInfo,
                    sender = Sender.AI,
                    roomId = matchedRoom.id,
                    roomName = matchedRoom.nameMalay,
                    roomLevel = matchedRoom.level,
                    roomBlock = matchedRoom.block
                )
            } else {
                ChatMessage(text = aiReplyText, sender = Sender.AI)
            }

            val updatedList = _messages.value ?: mutableListOf()
            updatedList.add(aiMsg)
            _messages.value = updatedList
            _isLoading.value = false
        }
    }
}
