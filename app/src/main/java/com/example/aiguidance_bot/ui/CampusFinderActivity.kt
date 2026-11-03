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
import com.example.aiguidance_bot.data.DestinationCategory
import com.example.aiguidance_bot.data.FtmkLocationDatabase

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
        val categoryContainer = findViewById<LinearLayout>(R.id.categoryContainer)
        val rvRecommendations = findViewById<RecyclerView>(R.id.rvRecommendations)
        val progressBar = findViewById<ProgressBar>(R.id.progressBarFinder)
        val tvError = findViewById<TextView>(R.id.tvErrorFinder)

        btnBack.setOnClickListener { finish() }

        recommendationAdapter = RecommendationAdapter(emptyList()) { selectedDest ->
            val matchedRoom = FtmkLocationDatabase.rooms.find { it.id == selectedDest.id }
            val intent = Intent(this, FtmkMapActivity::class.java).apply {
                putExtra(FtmkMapActivity.EXTRA_ROOM_ID, selectedDest.id)
                putExtra(FtmkMapActivity.EXTRA_ROOM_NAME, selectedDest.name)
                putExtra(FtmkMapActivity.EXTRA_ROOM_LEVEL, matchedRoom?.level ?: 1)
                putExtra(FtmkMapActivity.EXTRA_ROOM_BLOCK, matchedRoom?.block ?: "Blok E1")
            }
            startActivity(intent)
        }
        rvRecommendations.layoutManager = LinearLayoutManager(this)
        rvRecommendations.adapter = recommendationAdapter

        btnSearch.setOnClickListener {
            viewModel.searchDestinations(etSearchQuery.text.toString())
        }

        viewModel.categories.observe(this) { categories ->
            categoryContainer.removeAllViews()
            categories.forEach { category ->
                val chip = TextView(this).apply {
                    text = category.name
                    textSize = 14f
                    setPadding(32, 16, 32, 16)
                    val params = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    ).apply { marginEnd = 16 }
                    layoutParams = params

                    setOnClickListener {
                        viewModel.selectCategory(if (viewModel.currentCategory == category.name) null else category.name)
                    }
                }
                categoryContainer.addView(chip)
            }
            updateCategoryChips(categoryContainer, categories)
        }

        // Re-update chips styling when selected category changes
        viewModel.recommendations.observe(this) { recommendations ->
            recommendationAdapter.updateData(recommendations)
            tvError.visibility = View.GONE
            updateCategoryChips(categoryContainer, viewModel.categories.value ?: emptyList())
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

    private fun updateCategoryChips(container: LinearLayout, categories: List<DestinationCategory>) {
        for (i in 0 until container.childCount) {
            val chip = container.getChildAt(i) as TextView
            val isSelected = chip.text.toString() == viewModel.currentCategory || (viewModel.currentCategory == null && chip.text.toString() == "All")
            
            if (isSelected) {
                chip.setBackgroundResource(R.drawable.bg_chip_selected)
                chip.setTextColor(Color.WHITE)
            } else {
                chip.setBackgroundResource(R.drawable.bg_chip_unselected)
                chip.setTextColor(Color.parseColor("#475569"))
            }
        }
    }
}
