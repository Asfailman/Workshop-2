package com.example.aiguidance_bot.ui

import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.aiguidance_bot.R
import com.example.aiguidance_bot.ui.InteractiveMapActivity
import com.example.aiguidance_bot.data.DestinationCategory
import com.example.aiguidance_bot.data.FtmkLocationDatabase
import com.example.aiguidance_bot.data.PreferencesHelper

class CampusFinderActivity : AppCompatActivity() {

    private val viewModel: CampusFinderViewModel by viewModels()
    private lateinit var recommendationAdapter: RecommendationAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_campus_finder)

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.headerLayoutFinder)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(v.paddingLeft, systemBars.top + 16, v.paddingRight, v.paddingBottom)
            insets
        }

        val btnBack = findViewById<ImageView>(R.id.btnBackFinder)
        val etSearchQuery = findViewById<EditText>(R.id.etSearchQuery)
        val btnSearch = findViewById<ImageView>(R.id.btnSearch)
        val rvRecommendations = findViewById<RecyclerView>(R.id.rvRecommendations)
        val progressBar = findViewById<ProgressBar>(R.id.progressBarFinder)
        val tvError = findViewById<TextView>(R.id.tvErrorFinder)

        val currentTheme = PreferencesHelper.getThemeMode(this)
        val isDarkMode = (currentTheme == PreferencesHelper.THEME_DARK)
        
        val mainLayout = findViewById<View>(R.id.mainFinderLayout)

        if (isDarkMode) {
            mainLayout.setBackgroundColor(Color.parseColor("#262B33")) // Soft Slate Grey
            etSearchQuery.setTextColor(Color.WHITE)
            etSearchQuery.setHintTextColor(Color.parseColor("#94A3B8"))
        } else {
            mainLayout.setBackgroundColor(Color.parseColor("#F8FAFC")) // Light mode background
            etSearchQuery.setTextColor(Color.parseColor("#1E293B"))
            etSearchQuery.setHintTextColor(Color.parseColor("#94A3B8"))
        }

        btnBack.setOnClickListener { finish() }

        recommendationAdapter = RecommendationAdapter(emptyList()) { selectedDest ->
            val intent = Intent(this, InteractiveMapActivity::class.java).apply {
                putExtra("DESTINATION_NAME", selectedDest.name)
            }
            startActivity(intent)
        }
        rvRecommendations.layoutManager = LinearLayoutManager(this)
        rvRecommendations.adapter = recommendationAdapter

        btnSearch.setOnClickListener {
            viewModel.searchDestinations(etSearchQuery.text.toString())
        }

        viewModel.recommendations.observe(this) { recommendations ->
            recommendationAdapter.updateData(recommendations)
            tvError.visibility = View.GONE
        }

        viewModel.isLoading.observe(this) { isLoading ->
            progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
        }

        viewModel.errorMessage.observe(this) { error ->
            if (error != null) {
                tvError.visibility = View.VISIBLE
                tvError.text = error
            } else {
                tvError.visibility = View.GONE
            }
        }
    }



}
