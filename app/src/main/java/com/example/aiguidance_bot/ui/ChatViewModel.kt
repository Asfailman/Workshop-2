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
            val aiReplyText = repository.getAiResponse(text)
            val aiMsg = ChatMessage(text = aiReplyText, sender = Sender.AI)
            
            val updatedList = _messages.value ?: mutableListOf()
            updatedList.add(aiMsg)
            _messages.value = updatedList
            _isLoading.value = false
        }
    }
}
