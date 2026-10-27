package com.example.aiguidance_bot

import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.provider.MediaStore
import android.util.TypedValue
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.PopupWindow
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.aiguidance_bot.data.PreferencesHelper
import com.example.aiguidance_bot.ui.CampusFinderActivity
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
        val headerLayout = findViewById<View>(R.id.headerLayout)

        headerLayout.setOnClickListener {
            val intent = Intent(this, CampusFinderActivity::class.java)
            startActivity(intent)
        }

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

        val fontSp = PreferencesHelper.getFontSizeSp(this)
        val isDark = PreferencesHelper.getThemeMode(this) == PreferencesHelper.THEME_DARK

        chatViewModel.messages.observe(this) { messages ->
            chatAdapter = ChatAdapter(messages, fontSizeSp = fontSp, isDarkMode = isDark)
            recyclerView.adapter = chatAdapter
            if (messages.isNotEmpty()) {
                recyclerView.scrollToPosition(messages.size - 1)
            }
        }

        applyThemeAndFontSettings()

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

            popupView.findViewById<View>(R.id.menuDelete).setOnClickListener {
                popupWindow.dismiss()
                showClearChatConfirmationDialog()
            }
            popupView.findViewById<View>(R.id.menuSettings).setOnClickListener {
                popupWindow.dismiss()
                showSettingsDialog()
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

    private fun showClearChatConfirmationDialog() {
        val alertDialog = AlertDialog.Builder(this)
            .setTitle("Clear Chat History?")
            .setMessage("Are you sure you want to clear all chat messages? This action cannot be undone.")
            .setPositiveButton("Clear") { dialog, _ ->
                chatViewModel.clearChat()
                Toast.makeText(this, "Chat cleared", Toast.LENGTH_SHORT).show()
                dialog.dismiss()
            }
            .setNegativeButton("Cancel") { dialog, _ ->
                dialog.dismiss()
            }
            .create()

        alertDialog.show()

        alertDialog.getButton(AlertDialog.BUTTON_POSITIVE)?.setTextColor(Color.parseColor("#EF4444"))
        alertDialog.getButton(AlertDialog.BUTTON_NEGATIVE)?.setTextColor(Color.parseColor("#64748B"))
    }

    private fun showSettingsDialog() {
        val dialogView = layoutInflater.inflate(R.layout.dialog_settings, null)
        val dialog = AlertDialog.Builder(this)
            .setView(dialogView)
            .create()

        dialog.window?.setBackgroundDrawableResource(android.R.color.transparent)

        val btnThemeBright = dialogView.findViewById<Button>(R.id.btnThemeBright)
        val btnThemeDark = dialogView.findViewById<Button>(R.id.btnThemeDark)
        val btnFontSmall = dialogView.findViewById<Button>(R.id.btnFontSmall)
        val btnFontMedium = dialogView.findViewById<Button>(R.id.btnFontMedium)
        val btnFontLarge = dialogView.findViewById<Button>(R.id.btnFontLarge)
        val previewContainer = dialogView.findViewById<View>(R.id.previewContainer)
        val tvPreviewBubble = dialogView.findViewById<TextView>(R.id.tvPreviewBubble)
        val btnResetDefaults = dialogView.findViewById<Button>(R.id.btnResetDefaults)
        val btnApplySettings = dialogView.findViewById<Button>(R.id.btnApplySettings)

        var tempTheme = PreferencesHelper.getThemeMode(this)
        var tempFontSize = PreferencesHelper.getFontSizeSp(this)

        fun updateLivePreview() {
            tvPreviewBubble.setTextSize(TypedValue.COMPLEX_UNIT_SP, tempFontSize)

            if (tempTheme == PreferencesHelper.THEME_DARK) {
                previewContainer.setBackgroundColor(Color.parseColor("#363D47")) // Dark Charcoal Grey
                tvPreviewBubble.setTextColor(Color.WHITE)
                btnThemeDark.setTextColor(Color.parseColor("#1987b8"))
                btnThemeBright.setTextColor(Color.parseColor("#475569"))
            } else {
                previewContainer.setBackgroundColor(Color.parseColor("#F1F5F9")) // Light Grey
                tvPreviewBubble.setTextColor(Color.parseColor("#1E293B"))
                btnThemeBright.setTextColor(Color.parseColor("#1987b8"))
                btnThemeDark.setTextColor(Color.parseColor("#475569"))
            }

            btnFontSmall.setTextColor(if (tempFontSize == 14f) Color.parseColor("#1987b8") else Color.parseColor("#475569"))
            btnFontMedium.setTextColor(if (tempFontSize == 16f) Color.parseColor("#1987b8") else Color.parseColor("#475569"))
            btnFontLarge.setTextColor(if (tempFontSize == 20f) Color.parseColor("#1987b8") else Color.parseColor("#475569"))
        }

        updateLivePreview()

        btnThemeBright.setOnClickListener {
            tempTheme = PreferencesHelper.THEME_BRIGHT
            updateLivePreview()
        }

        btnThemeDark.setOnClickListener {
            tempTheme = PreferencesHelper.THEME_DARK
            updateLivePreview()
        }

        btnFontSmall.setOnClickListener {
            tempFontSize = 14f
            updateLivePreview()
        }

        btnFontMedium.setOnClickListener {
            tempFontSize = 16f
            updateLivePreview()
        }

        btnFontLarge.setOnClickListener {
            tempFontSize = 20f
            updateLivePreview()
        }

        btnResetDefaults.setOnClickListener {
            tempTheme = PreferencesHelper.THEME_BRIGHT
            tempFontSize = 16f
            updateLivePreview()
            Toast.makeText(this, "Reset to default settings", Toast.LENGTH_SHORT).show()
        }

        btnApplySettings.setOnClickListener {
            PreferencesHelper.setThemeMode(this, tempTheme)
            PreferencesHelper.setFontSizeSp(this, tempFontSize)

            applyThemeAndFontSettings()
            Toast.makeText(this, "Settings applied & saved", Toast.LENGTH_SHORT).show()
            dialog.dismiss()
        }

        dialog.show()
    }

    private fun applyThemeAndFontSettings() {
        val currentTheme = PreferencesHelper.getThemeMode(this)
        val currentFontSize = PreferencesHelper.getFontSizeSp(this)
        val isDarkMode = (currentTheme == PreferencesHelper.THEME_DARK)

        val mainLayout = findViewById<View>(R.id.main)
        val layoutInput = findViewById<View>(R.id.layoutInput)
        val etMessageInput = findViewById<EditText>(R.id.etMessageInput)

        if (isDarkMode) {
            mainLayout.setBackgroundColor(Color.parseColor("#262B33")) // Soft Slate Grey
            layoutInput?.setBackgroundColor(Color.parseColor("#1E2229")) // Dark Grey Bar
            etMessageInput?.setTextColor(Color.WHITE)
            etMessageInput?.setHintTextColor(Color.parseColor("#94A3B8"))
        } else {
            mainLayout.setBackgroundColor(Color.WHITE)
            layoutInput?.setBackgroundColor(Color.parseColor("#F8FAFC"))
            etMessageInput?.setTextColor(Color.parseColor("#1E293B"))
            etMessageInput?.setHintTextColor(Color.parseColor("#94A3B8"))
        }

        if (::chatAdapter.isInitialized) {
            chatAdapter.updateSettings(currentFontSize, isDarkMode)
        }
    }
}
