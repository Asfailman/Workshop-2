
package com.example.aiguidance_bot.ui

import android.content.Intent
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

class ChatAdapter(private val messages: List<ChatMessage>) :
    RecyclerView.Adapter<RecyclerView.ViewHolder>() {

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
            is UserMessageViewHolder -> holder.bind(message)
            is AiMessageViewHolder -> holder.bind(message)
        }
    }

    override fun getItemCount(): Int = messages.size

    class UserMessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvMessage: TextView =
            itemView.findViewById(R.id.tvUserMessage)

        private val tvTimestamp: TextView =
            itemView.findViewById(R.id.tvUserTimestamp)

        fun bind(message: ChatMessage) {
            tvMessage.text = message.text
            tvTimestamp.text = timeFormat.format(Date(message.timestamp))
        }
    }

    class AiMessageViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvMessage: TextView =
            itemView.findViewById(R.id.tvAiMessage)

        private val tvTimestamp: TextView =
            itemView.findViewById(R.id.tvAiTimestamp)

        private val btnViewMap: Button =
            itemView.findViewById(R.id.btnViewMap)

        fun bind(message: ChatMessage) {
            tvMessage.text = message.text
            tvTimestamp.text = timeFormat.format(Date(message.timestamp))

            btnViewMap.visibility = View.GONE
            btnViewMap.setOnClickListener(null)

            if (message.roomId != null) {
                btnViewMap.visibility = View.VISIBLE

                btnViewMap.setOnClickListener {
                    val context = itemView.context

                    val intent = Intent(context, InteractiveMapActivity::class.java).apply {
                        putExtra("DESTINATION_NAME", message.roomName)
                    }

                    context.startActivity(intent)
                }
            }
        }
    }
}
