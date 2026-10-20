package com.example.aiguidance_bot.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.example.aiguidance_bot.R
import com.example.aiguidance_bot.data.RecommendationItem

class RecommendationAdapter(
    private var items: List<RecommendationItem>,
    private val onItemSelected: (RecommendationItem) -> Unit
) : RecyclerView.Adapter<RecommendationAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvName: TextView = view.findViewById(R.id.tvDestName)
        val tvLocation: TextView = view.findViewById(R.id.tvDestLocation)
        val tvDistance: TextView = view.findViewById(R.id.tvDestDistance)
        val tvDescription: TextView = view.findViewById(R.id.tvDestDescription)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_recommendation, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val item = items[position]
        holder.tvName.text = item.name
        holder.tvLocation.text = "Location: ${item.location}"
        holder.tvDistance.text = "${item.distanceMeters} meters away"
        holder.tvDescription.text = item.description ?: ""

        holder.itemView.setOnClickListener {
            onItemSelected(item)
        }
    }

    override fun getItemCount() = items.size

    fun updateData(newItems: List<RecommendationItem>) {
        this.items = newItems
        notifyDataSetChanged()
    }
}
