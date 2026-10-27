package com.example.aiguidance_bot.ui

import android.content.Intent
import android.graphics.Color
import android.util.TypedValue
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.example.aiguidance_bot.R
import com.example.aiguidance_bot.data.ChatMessage
import com.example.aiguidance_bot.data.Sender
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ChatAdapter(
    private val messages: List<ChatMessage>,
    private var fontSizeSp: Float = 16f,
    private var isDarkMode: Boolean = false
) : RecyclerView.Adapter<RecyclerView.ViewHolder>() {

    companion object {
        private const val VIEW_TYPE_USER = 1
        private const val VIEW_TYPE_AI = 2
        private val timeFormat = SimpleDateFormat("h:mm a", Locale.getDefault())
    }

    override fun getItemViewType(position: Int): Int {
        return when (messages[position].sender) {
            Sender.USER -> VIEW_TYPE_USER
            Sender.AI -> VIEW_TYPE_AI
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        val inflater = LayoutInflater.from(parent.context)
        return if (viewType == VIEW_TYPE_USER) {
            val view = inflater.inflate(R.layout.item_chat_user, parent, false)
            UserMessageViewHolder(view)
        } else {
            val view = inflater.inflate(R.layout.item_chat_ai, parent, false)
            AiMessageViewHolder(view)
        }
    }

    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
        val message = messages[position]
        when (holder) {
            is UserMessageViewHolder -> holder.bind(message, fontSizeSp, isDarkMode)
            is AiMessageViewHolder -> holder.bind(message, fontSizeSp, isDarkMode)
        }
    }

    override fun getItemCount(): Int = messages.size

    fun updateSettings(newFontSizeSp: Float, newIsDarkMode: Boolean) {
        this.fontSizeSp = newFontSizeSp
        this.isDarkMode = newIsDarkMode
        notifyDataSetChanged()
    }

    class UserMessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvMessage: TextView = itemView.findViewById(R.id.tvUserMessage)
        private val tvTimestamp: TextView = itemView.findViewById(R.id.tvUserTimestamp)

        fun bind(message: ChatMessage, fontSizeSp: Float, isDarkMode: Boolean) {
            tvMessage.text = message.text
            tvMessage.setTextSize(TypedValue.COMPLEX_UNIT_SP, fontSizeSp)
            tvTimestamp.text = timeFormat.format(Date(message.timestamp))

            if (isDarkMode) {
                tvTimestamp.setTextColor(Color.parseColor("#CBD5E1"))
            } else {
                tvTimestamp.setTextColor(Color.parseColor("#64748B"))
            }
        }
    }

    class AiMessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvMessage: TextView = itemView.findViewById(R.id.tvAiMessage)
        private val tvTimestamp: TextView = itemView.findViewById(R.id.tvAiTimestamp)
        private val btnViewMap: Button = itemView.findViewById(R.id.btnViewMap)

        fun bind(message: ChatMessage, fontSizeSp: Float, isDarkMode: Boolean) {
            tvMessage.text = message.text
            tvMessage.setTextSize(TypedValue.COMPLEX_UNIT_SP, fontSizeSp)
            tvTimestamp.text = timeFormat.format(Date(message.timestamp))

            if (isDarkMode) {
                tvMessage.background?.setTint(Color.parseColor("#363D47"))
                tvMessage.setTextColor(Color.parseColor("#FFFFFF"))
                tvTimestamp.setTextColor(Color.parseColor("#CBD5E1"))
            } else {
                tvMessage.background?.setTint(Color.parseColor("#F1F5F9"))
                tvMessage.setTextColor(Color.parseColor("#1E293B"))
                tvTimestamp.setTextColor(Color.parseColor("#64748B"))
            }

            if (message.roomId != null) {
                btnViewMap.visibility = View.VISIBLE
                btnViewMap.setOnClickListener {
                    val context = itemView.context
                    val intent = Intent(context, FtmkMapActivity::class.java).apply {
                        putExtra(FtmkMapActivity.EXTRA_ROOM_ID, message.roomId)
                        putExtra(FtmkMapActivity.EXTRA_ROOM_NAME, message.roomName)
                        putExtra(FtmkMapActivity.EXTRA_ROOM_LEVEL, message.roomLevel ?: 1)
                        putExtra(FtmkMapActivity.EXTRA_ROOM_BLOCK, message.roomBlock)
                    }
                    context.startActivity(intent)
                }
            } else {
                btnViewMap.visibility = View.GONE
            }
        }
    }
}
