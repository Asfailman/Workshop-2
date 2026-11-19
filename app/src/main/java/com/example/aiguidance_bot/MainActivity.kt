package com.example.aiguidance_bot

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.media.MediaRecorder
import android.os.Bundle
import android.provider.MediaStore
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
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
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.aiguidance_bot.data.Sender
import com.example.aiguidance_bot.ui.ChatAdapter
import com.example.aiguidance_bot.ui.ChatViewModel
import com.example.aiguidance_bot.utils.CampusSpeechCorrector
import com.example.aiguidance_bot.utils.WavRecorder
import java.io.File
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private val chatViewModel: ChatViewModel by viewModels()
    private lateinit var chatAdapter: ChatAdapter
    private lateinit var textToSpeech: TextToSpeech
    private lateinit var etMessageInput: EditText
    private lateinit var btnVoiceInput: ImageView
    private var isTtsReady = false

    // Real-time live speech recognition
    private var speechRecognizer: SpeechRecognizer? = null
    private var isListeningSpeech: Boolean = false

    // Fallback WAV recorder for server-side processing
    private val wavRecorder = WavRecorder()
    private var voiceRecordingFile: File? = null
    private var isRecordingAudio = false
    private val recordingHandler = android.os.Handler(android.os.Looper.getMainLooper())
    private var autoStopRunnable: Runnable? = null

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

    private val speechInputLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { res ->
        if (res.resultCode == RESULT_OK && res.data != null) {
            val candidates = res.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS) ?: arrayListOf()
            val rawText = candidates.firstOrNull()?.trim()
            if (!rawText.isNullOrBlank()) {
                if (::textToSpeech.isInitialized && textToSpeech.isSpeaking) {
                    textToSpeech.stop()
                }
                val spokenText = CampusSpeechCorrector.correctTranscript(rawText)
                if (::etMessageInput.isInitialized) {
                    etMessageInput.setText(spokenText)
                    etMessageInput.setSelection(spokenText.length)
                    chatViewModel.sendMessage(spokenText)
                    etMessageInput.text.clear()
                }
            }
        }
    }

    private val micPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            toggleAudioRecording()
        } else {
            Toast.makeText(this, "Microphone permission required for voice input", Toast.LENGTH_SHORT).show()
        }
    }

    private fun initSpeechRecognizer() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            return
        }
        try {
            speechRecognizer?.destroy()
        } catch (_: Exception) {}

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this).apply {
            setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) {
                    isListeningSpeech = true
                    updateMicUi(isListening = true)
                    if (::etMessageInput.isInitialized) {
                        etMessageInput.hint = "🎙️ Listening... Speak now"
                    }
                }

                override fun onBeginningOfSpeech() {}

                override fun onRmsChanged(rmsdB: Float) {
                    if (::btnVoiceInput.isInitialized && isListeningSpeech) {
                        val scale = 1.15f + (rmsdB.coerceIn(0f, 10f) / 40f)
                        btnVoiceInput.scaleX = scale
                        btnVoiceInput.scaleY = scale
                    }
                }

                override fun onBufferReceived(buffer: ByteArray?) {}

                override fun onEndOfSpeech() {}

                override fun onError(error: Int) {
                    isListeningSpeech = false
                    updateMicUi(isListening = false)
                    if (::etMessageInput.isInitialized) {
                        etMessageInput.hint = "Type or speak a message..."
                    }

                    val msg = when (error) {
                        SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
                        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission required"
                        SpeechRecognizer.ERROR_NETWORK -> "Network issue for voice recognition"
                        SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Voice network timeout"
                        SpeechRecognizer.ERROR_NO_MATCH -> "Didn't catch that. Tap mic to try again."
                        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech detected"
                        else -> null
                    }
                    if (msg != null && ::etMessageInput.isInitialized && etMessageInput.text.isNullOrBlank()) {
                        Toast.makeText(this@MainActivity, msg, Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onResults(results: Bundle?) {
                    isListeningSpeech = false
                    updateMicUi(isListening = false)
                    if (::etMessageInput.isInitialized) {
                        etMessageInput.hint = "Type or speak a message..."
                        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        val text = matches?.firstOrNull()?.trim()
                        if (!text.isNullOrBlank()) {
                            val corrected = CampusSpeechCorrector.correctTranscript(text)
                            etMessageInput.setText(corrected)
                            etMessageInput.setSelection(corrected.length)
                            // Auto-send as soon as user stops talking!
                            chatViewModel.sendMessage(corrected)
                            etMessageInput.text.clear()
                        }
                    }
                }

                override fun onPartialResults(partialResults: Bundle?) {
                    if (::etMessageInput.isInitialized) {
                        val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        val partial = matches?.firstOrNull()?.trim()
                        if (!partial.isNullOrBlank()) {
                            // Live word-by-word streaming into the input bar!
                            val liveText = CampusSpeechCorrector.correctTranscript(partial)
                            etMessageInput.setText(liveText)
                            etMessageInput.setSelection(liveText.length)
                        }
                    }
                }

                override fun onEvent(eventType: Int, params: Bundle?) {}
            })
        }
    }

    private fun startLiveSpeechRecognition() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            return
        }

        if (::textToSpeech.isInitialized && textToSpeech.isSpeaking) {
            textToSpeech.stop()
        }

        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            launchVoicePrompt()
            return
        }

        if (speechRecognizer == null) {
            initSpeechRecognizer()
        }

        val speechIntent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-MY")
            putExtra("android.speech.extra.EXTRA_ADDITIONAL_LANGUAGES", arrayOf("en-MY", "ms-MY", "en-US"))
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
            // Extended silence windows so user is not cut off prematurely
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 4000L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 3000L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 2000L)
        }

        try {
            speechRecognizer?.startListening(speechIntent)
            isListeningSpeech = true
            updateMicUi(isListening = true)
            if (::etMessageInput.isInitialized) {
                etMessageInput.hint = "🎙️ Listening... Speak now"
            }
        } catch (e: Exception) {
            isListeningSpeech = false
            updateMicUi(isListening = false)
            launchVoicePrompt()
        }
    }

    private fun stopLiveSpeechRecognition() {
        if (isListeningSpeech) {
            try {
                speechRecognizer?.stopListening()
            } catch (_: Exception) {}
            isListeningSpeech = false
            updateMicUi(isListening = false)
            if (::etMessageInput.isInitialized) {
                etMessageInput.hint = "Type or speak a message..."
            }
        }
    }

    private fun toggleSpeechInput() {
        if (isListeningSpeech) {
            stopLiveSpeechRecognition()
        } else if (wavRecorder.isCurrentlyRecording()) {
            toggleAudioRecording()
        } else {
            startLiveSpeechRecognition()
        }
    }

    private fun updateMicUi(isListening: Boolean) {
        if (::btnVoiceInput.isInitialized) {
            if (isListening) {
                btnVoiceInput.setColorFilter(Color.parseColor("#E53E3E"))
                btnVoiceInput.animate().scaleX(1.2f).scaleY(1.2f).setDuration(150).start()
            } else {
                btnVoiceInput.clearColorFilter()
                btnVoiceInput.animate().scaleX(1.0f).scaleY(1.0f).setDuration(150).start()
            }
        }
    }

    private fun launchVoicePrompt() {
        if (::textToSpeech.isInitialized && textToSpeech.isSpeaking) {
            textToSpeech.stop()
        }
        val speechIntent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-MY")
            putExtra("android.speech.extra.EXTRA_ADDITIONAL_LANGUAGES", arrayOf("en-MY", "ms-MY", "en-US"))
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 4000L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 3000L)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak campus query (e.g. 'Where is Makmal AI 2?')...")
        }
        try {
            speechInputLauncher.launch(speechIntent)
        } catch (_: Exception) {
            Toast.makeText(this, "Voice recognition unavailable on this device", Toast.LENGTH_SHORT).show()
        }
    }

    private fun toggleAudioRecording() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            return
        }

        if (!wavRecorder.isCurrentlyRecording()) {
            try {
                if (::textToSpeech.isInitialized && textToSpeech.isSpeaking) {
                    textToSpeech.stop()
                }
                voiceRecordingFile = File(cacheDir, "robot_voice_${System.currentTimeMillis()}.wav")
                val started = wavRecorder.startRecording(voiceRecordingFile!!)
                if (!started) {
                    Toast.makeText(this, "Could not access microphone", Toast.LENGTH_SHORT).show()
                    return
                }

                isRecordingAudio = true
                if (::btnVoiceInput.isInitialized) {
                    btnVoiceInput.setColorFilter(Color.RED)
                    btnVoiceInput.animate().scaleX(1.25f).scaleY(1.25f).setDuration(200).start()
                }
                if (::etMessageInput.isInitialized) {
                    etMessageInput.hint = "🔴 Listening... Speak now (Tap to send)"
                }
                Toast.makeText(this, "🎙️ Listening... Speak your question!", Toast.LENGTH_SHORT).show()

                // Auto-stop after 30s max if user forgets to tap again
                autoStopRunnable?.let { recordingHandler.removeCallbacks(it) }
                autoStopRunnable = Runnable {
                    if (wavRecorder.isCurrentlyRecording()) {
                        toggleAudioRecording()
                    }
                }
                recordingHandler.postDelayed(autoStopRunnable!!, 30000L)
            } catch (e: Exception) {
                isRecordingAudio = false
                Toast.makeText(this, "Failed to start recorder: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        } else {
            // Cancel auto-stop timer
            autoStopRunnable?.let { recordingHandler.removeCallbacks(it) }
            autoStopRunnable = null

            val file = wavRecorder.stopRecording() ?: voiceRecordingFile
            isRecordingAudio = false

            if (::btnVoiceInput.isInitialized) {
                btnVoiceInput.clearColorFilter()
                btnVoiceInput.animate().scaleX(1.0f).scaleY(1.0f).setDuration(200).start()
            }
            if (::etMessageInput.isInitialized) {
                etMessageInput.hint = "⚡ Processing with AI Whisper..."
            }

            if (file != null && file.exists() && file.length() > 44) {
                Toast.makeText(this, "⚡ Sending audio to AI Whisper...", Toast.LENGTH_SHORT).show()
                chatViewModel.sendVoiceAudio(file)
            } else {
                Toast.makeText(this, "No voice detected. Please speak closer to the mic.", Toast.LENGTH_SHORT).show()
                if (::etMessageInput.isInitialized) {
                    etMessageInput.hint = "Type or speak a message..."
                }
            }
        }
    }

    private fun sanitizeForSpeech(input: String): String {
        return input.replace(Regex("""[*#_`~]"""), "")
            .replace(Regex("""[📍🚶🤖🗣️⚡🎯]"""), "")
            .trim()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)

        initSpeechRecognizer()

        textToSpeech = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                val result = textToSpeech.setLanguage(Locale.US)
                isTtsReady = result != TextToSpeech.LANG_MISSING_DATA &&
                        result != TextToSpeech.LANG_NOT_SUPPORTED
            }
        }

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        val recyclerView = findViewById<RecyclerView>(R.id.recyclerViewChat)
        etMessageInput = findViewById(R.id.etMessageInput)
        val btnSend = findViewById<ImageView>(R.id.btnSend)
        val btnMenu = findViewById<ImageView>(R.id.btnMenu)
        val btnAdd = findViewById<ImageView>(R.id.btnAdd)
        val progressBar = findViewById<ProgressBar>(R.id.progressBar)

        // Integrated In-Layout Attachment Card & Action Items
        val cardAttachmentMenu = findViewById<View>(R.id.cardAttachmentMenu)
        val btnCamera = findViewById<View>(R.id.btnCamera)
        val btnUploadPhoto = findViewById<View>(R.id.btnUploadPhoto)
        val btnUploadFile = findViewById<View>(R.id.btnUploadFile)
        val btnVoiceOption = findViewById<View>(R.id.btnVoiceOption)
        btnVoiceInput = findViewById(R.id.btnVoiceInput)

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

        var lastSpokenMessageId: String? = null

        chatViewModel.messages.observe(this) { messages ->
            chatAdapter = ChatAdapter(messages)
            recyclerView.adapter = chatAdapter

            if (messages.isNotEmpty()) {
                recyclerView.scrollToPosition(messages.size - 1)

                val latestMessage = messages.last()

                if (latestMessage.sender == Sender.AI &&
                    latestMessage.id != lastSpokenMessageId &&
                    latestMessage.text.isNotBlank()
                ) {
                    lastSpokenMessageId = latestMessage.id

                    if (isTtsReady) {
                        val speechText = sanitizeForSpeech(latestMessage.text)
                        if (speechText.isNotBlank()) {
                            textToSpeech.speak(
                                speechText,
                                TextToSpeech.QUEUE_FLUSH,
                                null,
                                latestMessage.id
                            )
                        }
                    }
                }
            }
        }

        chatViewModel.isLoading.observe(this) { isLoading ->
            progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
            btnSend.isEnabled = !isLoading
            btnSend.alpha = if (isLoading) 0.5f else 1.0f
            if (!isLoading && ::etMessageInput.isInitialized && !wavRecorder.isCurrentlyRecording()) {
                etMessageInput.hint = "Type or speak a message..."
            }
        }

        btnSend.setOnClickListener {
            closeAttachmentMenu()
            stopLiveSpeechRecognition()
            if (wavRecorder.isCurrentlyRecording()) {
                wavRecorder.stopRecording()
                isRecordingAudio = false
            }
            if (::textToSpeech.isInitialized && textToSpeech.isSpeaking) {
                textToSpeech.stop()
            }
            val text = etMessageInput.text.toString().trim()
            if (text.isNotEmpty()) {
                chatViewModel.sendMessage(text)
                etMessageInput.text.clear()
            }
        }

        // Tap mic icon: Live streaming speech-to-text with real-time word-by-word display & auto-send
        btnVoiceInput.setOnClickListener {
            closeAttachmentMenu()
            toggleSpeechInput()
        }

        // Long press: Whisper audio file recording
        btnVoiceInput.setOnLongClickListener {
            closeAttachmentMenu()
            toggleAudioRecording()
            true
        }

        // Attachment menu option also invokes Whisper audio recording
        btnVoiceOption.setOnClickListener {
            closeAttachmentMenu()
            toggleAudioRecording()
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

    override fun onDestroy() {
        try {
            speechRecognizer?.destroy()
        } catch (_: Exception) {}
        speechRecognizer = null
        wavRecorder.stopRecording()
        if (::textToSpeech.isInitialized) {
            textToSpeech.stop()
            textToSpeech.shutdown()
        }
        super.onDestroy()
    }
}
