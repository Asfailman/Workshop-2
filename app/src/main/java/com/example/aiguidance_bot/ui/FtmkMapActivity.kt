package com.example.aiguidance_bot.ui

import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.constraintlayout.widget.ConstraintLayout
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.aiguidance_bot.R
import com.example.aiguidance_bot.data.FtmkLocationDatabase
import com.example.aiguidance_bot.data.FtmkRoom

class FtmkMapActivity : AppCompatActivity() {

    private var selectedLevel = 1
    private var currentRoom: FtmkRoom? = null
    private lateinit var roomAdapter: FloorRoomAdapter

    private lateinit var tvSelectedRoomName: TextView
    private lateinit var tvSelectedLevelBadge: TextView
    private lateinit var tvSelectedBlockBadge: TextView
    private lateinit var tvFloorTitle: TextView

    private lateinit var ivFtmkMapImage: ImageView
    private lateinit var layoutRedDotMarker: View
    private lateinit var tvRedDotLabel: TextView
    private lateinit var rvFloorRooms: RecyclerView

    private lateinit var btnLevel1: Button
    private lateinit var btnLevel2: Button
    private lateinit var btnLevel3: Button
    private lateinit var btnLevel4: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_ftmk_map)

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.headerLayoutMap)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(v.paddingLeft, systemBars.top + 16, v.paddingRight, v.paddingBottom)
            insets
        }

        val btnBack = findViewById<ImageView>(R.id.btnBackMap)
        btnBack.setOnClickListener { finish() }

        tvSelectedRoomName = findViewById(R.id.tvSelectedRoomName)
        tvSelectedLevelBadge = findViewById(R.id.tvSelectedLevelBadge)
        tvSelectedBlockBadge = findViewById(R.id.tvSelectedBlockBadge)
        tvFloorTitle = findViewById(R.id.tvFloorTitle)

        ivFtmkMapImage = findViewById(R.id.ivFtmkMapImage)
        layoutRedDotMarker = findViewById(R.id.layoutRedDotMarker)
        tvRedDotLabel = findViewById(R.id.tvRedDotLabel)

        btnLevel1 = findViewById(R.id.btnLevel1)
        btnLevel2 = findViewById(R.id.btnLevel2)
        btnLevel3 = findViewById(R.id.btnLevel3)
        btnLevel4 = findViewById(R.id.btnLevel4)

        rvFloorRooms = findViewById(R.id.rvFloorRooms)
        rvFloorRooms.layoutManager = LinearLayoutManager(this)

        roomAdapter = FloorRoomAdapter(emptyList()) { room ->
            displayRoomDetails(room)
        }
        rvFloorRooms.adapter = roomAdapter

        // Check if passed a specific room from chat or Smart Campus Finder
        val passedRoomId = intent.getStringExtra(EXTRA_ROOM_ID)
        val passedLevel = intent.getIntExtra(EXTRA_ROOM_LEVEL, 1)

        val targetRoom = FtmkLocationDatabase.findRoomById(passedRoomId)
        selectedLevel = targetRoom?.level ?: (if (passedLevel in 1..4) passedLevel else 1)

        btnLevel1.setOnClickListener { switchLevel(1) }
        btnLevel2.setOnClickListener { switchLevel(2) }
        btnLevel3.setOnClickListener { switchLevel(3) }
        btnLevel4.setOnClickListener { switchLevel(4) }

        ivFtmkMapImage.addOnLayoutChangeListener { _, _, _, _, _, _, _, _, _ ->
            currentRoom?.let { positionMarkerForRoom(it) }
        }

        switchLevel(selectedLevel)

        if (targetRoom != null) {
            displayRoomDetails(targetRoom)
        } else {
            val firstRoomOnLevel = FtmkLocationDatabase.rooms.firstOrNull { it.level == selectedLevel }
            if (firstRoomOnLevel != null) {
                displayRoomDetails(firstRoomOnLevel)
            }
        }
    }

    private fun switchLevel(level: Int) {
        selectedLevel = level
        tvFloorTitle.text = "FTMK MAP - LEVEL $selectedLevel (ARAS $selectedLevel)"

        val mapDrawableRes = when (level) {
            1 -> R.drawable.map_ftmk_level_1
            2 -> R.drawable.map_ftmk_level_2
            3 -> R.drawable.map_ftmk_level_3
            4 -> R.drawable.map_ftmk_level_4
            else -> R.drawable.map_ftmk_level_1
        }
        ivFtmkMapImage.setImageResource(mapDrawableRes)

        val levelRooms = FtmkLocationDatabase.rooms.filter { it.level == level }
        roomAdapter.updateRooms(levelRooms)

        updateLevelButtonsState()
    }

    private fun updateLevelButtonsState() {
        val selectedColor = Color.parseColor("#1987b8")
        val defaultColor = Color.parseColor("#475569")

        btnLevel1.setTextColor(if (selectedLevel == 1) selectedColor else defaultColor)
        btnLevel2.setTextColor(if (selectedLevel == 2) selectedColor else defaultColor)
        btnLevel3.setTextColor(if (selectedLevel == 3) selectedColor else defaultColor)
        btnLevel4.setTextColor(if (selectedLevel == 4) selectedColor else defaultColor)
    }

    private fun displayRoomDetails(room: FtmkRoom) {
        currentRoom = room
        tvSelectedRoomName.text = "${room.nameMalay}\n(${room.nameEnglish})"
        tvSelectedLevelBadge.text = "LEVEL ${room.level} (ARAS ${room.level})"
        tvSelectedBlockBadge.text = "🔴 ${room.block}"

        if (room.level != selectedLevel) {
            switchLevel(room.level)
        }

        // Dynamically position the RED DOT MARKER over the FTMK Map image
        layoutRedDotMarker.visibility = View.VISIBLE
        tvRedDotLabel.text = "📍 ${room.nameMalay}"

        positionMarkerForRoom(room)

        // Highlight and scroll to the room in the floor directory list
        val roomIndex = roomAdapter.selectRoom(room.id)
        if (roomIndex != -1) {
            rvFloorRooms.post {
                rvFloorRooms.smoothScrollToPosition(roomIndex)
            }
        }
    }

    private fun positionMarkerForRoom(room: FtmkRoom) {
        ivFtmkMapImage.post {
            val viewW = ivFtmkMapImage.width.toFloat()
            val viewH = ivFtmkMapImage.height.toFloat()
            if (viewW <= 0f || viewH <= 0f) return@post

            // SVG viewport aspect ratio is 400 x 300
            val svgW = 400f
            val svgH = 300f
            val scale = minOf(viewW / svgW, viewH / svgH)
            val drawnW = svgW * scale
            val drawnH = svgH * scale
            val offsetX = (viewW - drawnW) / 2f
            val offsetY = (viewH - drawnH) / 2f

            val pixelX = offsetX + (room.mapBiasX * drawnW)
            val pixelY = offsetY + (room.mapBiasY * drawnH)

            layoutRedDotMarker.post {
                val markerW = layoutRedDotMarker.width.toFloat()
                val markerH = layoutRedDotMarker.height.toFloat()
                // Red dot has 16dp diameter, so radius is 8dp
                val dotRadius = resources.displayMetrics.density * 8f

                val minX = 0f
                val maxX = (viewW - markerW).coerceAtLeast(0f)
                layoutRedDotMarker.translationX = (pixelX - (markerW / 2f)).coerceIn(minX, maxX)
                layoutRedDotMarker.translationY = (pixelY - (markerH - dotRadius)).coerceAtLeast(0f)
            }
        }
    }

    companion object {
        const val EXTRA_ROOM_ID = "EXTRA_ROOM_ID"
        const val EXTRA_ROOM_NAME = "EXTRA_ROOM_NAME"
        const val EXTRA_ROOM_LEVEL = "EXTRA_ROOM_LEVEL"
        const val EXTRA_ROOM_BLOCK = "EXTRA_ROOM_BLOCK"
    }
}
