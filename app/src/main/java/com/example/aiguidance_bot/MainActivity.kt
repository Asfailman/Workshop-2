package com.example.aiguidance_bot

import android.content.Intent
import android.os.Bundle
import android.provider.MediaStore
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.ImageView
import android.widget.PopupWindow
import android.widget.ProgressBar
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.aiguidance_bot.ui.ChatAdapter
import com.example.aiguidance_bot.ui.ChatViewModel

class MainActivity : AppCompatActivity() {

    private val chatViewModel: ChatViewModel by viewModels()
    private lateinit var chatAdapter: ChatAdapter

    private val cameraLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == RESULT_OK) {
            chatViewModel.sendMessage("📸 [Photo captured from Camera]")
        }
    }

    private val galleryLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == RESULT_OK && result.data != null) {
            chatViewModel.sendMessage("🖼️ [Photo uploaded from Gallery]")
        }
    }

    private val fileLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == RESULT_OK && result.data != null) {
            chatViewModel.sendMessage("📄 [Document/File uploaded]")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        val recyclerView = findViewById<RecyclerView>(R.id.recyclerViewChat)
        val etMessageInput = findViewById<EditText>(R.id.etMessageInput)
        val btnSend = findViewById<ImageView>(R.id.btnSend)
        val btnMenu = findViewById<ImageView>(R.id.btnMenu)
        val btnAdd = findViewById<ImageView>(R.id.btnAdd)
        val progressBar = findViewById<ProgressBar>(R.id.progressBar)

        // Integrated In-Layout Attachment Card & Action Items
        val cardAttachmentMenu = findViewById<View>(R.id.cardAttachmentMenu)
        val btnCamera = findViewById<View>(R.id.btnCamera)
        val btnUploadPhoto = findViewById<View>(R.id.btnUploadPhoto)
        val btnUploadFile = findViewById<View>(R.id.btnUploadFile)

        var isMenuVisible = false

        fun closeAttachmentMenu() {
            if (isMenuVisible) {
                isMenuVisible = false
                cardAttachmentMenu.visibility = View.GONE
                btnAdd.animate().rotation(0f).setDuration(200).start()
            }
        }

        fun openAttachmentMenu() {
            isMenuVisible = true
            cardAttachmentMenu.visibility = View.VISIBLE
            btnAdd.animate().rotation(45f).setDuration(200).start()
        }

        val layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }
        recyclerView.layoutManager = layoutManager

        chatViewModel.messages.observe(this) { messages ->
            chatAdapter = ChatAdapter(messages)
            recyclerView.adapter = chatAdapter
            if (messages.isNotEmpty()) {
                recyclerView.scrollToPosition(messages.size - 1)
            }
        }

        chatViewModel.isLoading.observe(this) { isLoading ->
            progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
            btnSend.isEnabled = !isLoading
            btnSend.alpha = if (isLoading) 0.5f else 1.0f
        }

        btnSend.setOnClickListener {
            closeAttachmentMenu()
            val text = etMessageInput.text.toString().trim()
            if (text.isNotEmpty()) {
                chatViewModel.sendMessage(text)
                etMessageInput.text.clear()
            }
        }

        // Close attachment menu if user scrolls or taps the chat list
        recyclerView.setOnTouchListener { _, _ ->
            closeAttachmentMenu()
            false
        }

        // Header Top-Right Dropdown Menu
        btnMenu.setOnClickListener { view ->
            closeAttachmentMenu()
            val inflater = layoutInflater
            val popupView = inflater.inflate(R.layout.popup_menu_options, null)

            val popupWindow = PopupWindow(
                popupView,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                true
            )

            popupView.findViewById<View>(R.id.menuRename).setOnClickListener {
                Toast.makeText(this, "Rename clicked", Toast.LENGTH_SHORT).show()
                popupWindow.dismiss()
            }
            popupView.findViewById<View>(R.id.menuShare).setOnClickListener {
                Toast.makeText(this, "Share Chat clicked", Toast.LENGTH_SHORT).show()
                popupWindow.dismiss()
            }
            popupView.findViewById<View>(R.id.menuDelete).setOnClickListener {
                Toast.makeText(this, "Delete clicked", Toast.LENGTH_SHORT).show()
                popupWindow.dismiss()
            }
            popupView.findViewById<View>(R.id.menuHelp).setOnClickListener {
                Toast.makeText(this, "Help clicked", Toast.LENGTH_SHORT).show()
                popupWindow.dismiss()
            }
            popupView.findViewById<View>(R.id.menuFeedback).setOnClickListener {
                Toast.makeText(this, "Feedback clicked", Toast.LENGTH_SHORT).show()
                popupWindow.dismiss()
            }

            popupWindow.showAsDropDown(view, -180, 10)
        }

        // Bottom-Left '+' / 'X' Toggle
        btnAdd.setOnClickListener {
            if (isMenuVisible) {
                closeAttachmentMenu()
            } else {
                openAttachmentMenu()
            }
        }

        // Attachment Action 1: Open Camera
        btnCamera.setOnClickListener {
            closeAttachmentMenu()
            val cameraIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            cameraLauncher.launch(cameraIntent)
        }

        // Attachment Action 2: Upload Photo
        btnUploadPhoto.setOnClickListener {
            closeAttachmentMenu()
            val galleryIntent = Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI)
            galleryLauncher.launch(galleryIntent)
        }

        // Attachment Action 3: Upload File
        btnUploadFile.setOnClickListener {
            closeAttachmentMenu()
            val fileIntent = Intent(Intent.ACTION_GET_CONTENT).apply {
                type = "*/*"
            }
            fileLauncher.launch(fileIntent)
        }
    }
}