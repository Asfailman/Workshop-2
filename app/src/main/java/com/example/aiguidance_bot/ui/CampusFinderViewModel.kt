package com.example.aiguidance_bot.ui

import android.R
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aiguidance_bot.data.ChatRepository
import com.example.aiguidance_bot.data.DestinationCategory
import com.example.aiguidance_bot.data.RecommendationItem
import com.example.aiguidance_bot.data.RoutePreviewResponse
import kotlinx.coroutines.launch

class CampusFinderViewModel(private val repository: ChatRepository = ChatRepository()) : ViewModel() {

    private val _categories = MutableLiveData<List<DestinationCategory>>()
    val categories: LiveData<List<DestinationCategory>> get() = _categories

    private val _recommendations = MutableLiveData<List<RecommendationItem>>()
    val recommendations: LiveData<List<RecommendationItem>> get() = _recommendations

    private val _routePreview = MutableLiveData<RoutePreviewResponse?>()
    val routePreview: LiveData<RoutePreviewResponse?> get() = _routePreview

    private val _isLoading = MutableLiveData(false)
    val isLoading: LiveData<Boolean> get() = _isLoading

    private val _errorMessage = MutableLiveData<String?>()
    val errorMessage: LiveData<String?> get() = _errorMessage

    var currentCategory: String? = null

    init {
        loadCategories()
        searchDestinations("")
    }

    private fun loadCategories() {
        // Mock Categories
        _categories.value = listOf(
            DestinationCategory("cat_all", "All", R.drawable.ic_menu_agenda),
            DestinationCategory("cat_lib", "Library", R.drawable.ic_menu_info_details),
            DestinationCategory("cat_food", "Food", R.drawable.ic_menu_directions),
            DestinationCategory("cat_class", "Classrooms", R.drawable.ic_menu_gallery)
        )
    }

    fun searchDestinations(query: String) {
        _isLoading.value = true
        _errorMessage.value = null
        viewModelScope.launch {
            try {
                val results = repository.searchDestinations(query, currentCategory)
                _recommendations.value = results
                if (results.isEmpty()) {
                    _errorMessage.value = "No destinations found."
                }
            } catch (e: Exception) {
                _errorMessage.value = "Failed to load destinations: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun selectCategory(category: String?) {
        currentCategory = category
        searchDestinations("") // Refresh search with new category
    }

    fun loadRoutePreview(startId: String, destId: String) {
        _isLoading.value = true
        _errorMessage.value = null
        viewModelScope.launch {
            try {
                val preview = repository.getRoutePreview(startId, destId)
                _routePreview.value = preview
            } catch (e: Exception) {
                _errorMessage.value = "Failed to load route preview: ${e.message}"
            } finally {
                _isLoading.value = false
            }
        }
    }
}
