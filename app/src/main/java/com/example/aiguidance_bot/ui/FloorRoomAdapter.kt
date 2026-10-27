package com.example.aiguidance_bot.ui

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.example.aiguidance_bot.R
import com.example.aiguidance_bot.data.FtmkRoom

class FloorRoomAdapter(
    private var rooms: List<FtmkRoom>,
    private val onRoomSelected: (FtmkRoom) -> Unit
) : RecyclerView.Adapter<FloorRoomAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvBlockBadge: TextView = view.findViewById(R.id.tvRoomBlockBadge)
        val tvMalayName: TextView = view.findViewById(R.id.tvRoomMalayName)
        val tvEnglishName: TextView = view.findViewById(R.id.tvRoomEnglishName)
        val tvCategory: TextView = view.findViewById(R.id.tvRoomCategory)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_floor_room, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val room = rooms[position]
        holder.tvBlockBadge.text = room.block
        holder.tvMalayName.text = room.nameMalay
        holder.tvEnglishName.text = room.nameEnglish
        holder.tvCategory.text = room.category

        when (room.block) {
            "Blok A" -> holder.tvBlockBadge.setBackgroundColor(Color.parseColor("#1E40AF"))
            "Blok C1" -> holder.tvBlockBadge.setBackgroundColor(Color.parseColor("#B91C1C"))
            "Blok C2" -> holder.tvBlockBadge.setBackgroundColor(Color.parseColor("#0F766E"))
            "Blok E1" -> holder.tvBlockBadge.setBackgroundColor(Color.parseColor("#6B21A8"))
            "Blok E2" -> holder.tvBlockBadge.setBackgroundColor(Color.parseColor("#A16207"))
            else -> holder.tvBlockBadge.setBackgroundColor(Color.parseColor("#1987b8"))
        }

        holder.itemView.setOnClickListener {
            onRoomSelected(room)
        }
    }

    override fun getItemCount() = rooms.size

    fun updateRooms(newRooms: List<FtmkRoom>) {
        this.rooms = newRooms
        notifyDataSetChanged()
    }
}
