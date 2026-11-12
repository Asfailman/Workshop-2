package com.example.aiguidance_bot.ui

import com.example.aiguidance_bot.R
import android.graphics.Color
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.camera.CameraUpdateFactory
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.Style
import org.maplibre.android.style.expressions.Expression.*
import org.maplibre.android.style.layers.CircleLayer
import org.maplibre.android.style.layers.FillExtrusionLayer
import org.maplibre.android.style.layers.LineLayer
import org.maplibre.android.style.layers.PropertyFactory.*
import org.maplibre.android.style.sources.GeoJsonSource
import org.maplibre.geojson.Feature
import org.maplibre.geojson.FeatureCollection
import org.maplibre.geojson.LineString
import org.maplibre.geojson.Point
import org.maplibre.android.style.layers.Property.LINE_CAP_ROUND
import org.maplibre.android.style.layers.Property.LINE_JOIN_ROUND
import java.io.InputStreamReader

class FtmkMapActivity : AppCompatActivity() {

    private lateinit var mapView: MapView
    private var mapLibreMap: MapLibreMap? = null
    private var activeFloor: Int = 1

    private lateinit var tvFloorBadge: TextView
    private lateinit var tvSelectedTitle: TextView
    private lateinit var tvSelectedSubtitle: TextView

    companion object {
        private const val ROOMS_SOURCE_ID = "ftmk-rooms-source"
        private const val ROOMS_LAYER_ID = "ftmk-rooms-3d-layer"
        private const val ROUTE_SOURCE_ID = "ftmk-route-source"
        private const val ROUTE_LAYER_ID = "ftmk-route-line-layer"
        private const val DEST_SOURCE_ID = "ftmk-dest-dot-source"
        private const val DEST_LAYER_ID = "ftmk-dest-dot-layer"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        MapLibre.getInstance(this)
        setContentView(R.layout.activity_ftmk_map)

        tvFloorBadge = findViewById(R.id.tvFloorBadge)
        tvSelectedTitle = findViewById(R.id.tvSelectedTitle)
        tvSelectedSubtitle = findViewById(R.id.tvSelectedSubtitle)

        mapView = findViewById(R.id.mapView)
        mapView.onCreate(savedInstanceState)

        mapView.getMapAsync { map ->
            mapLibreMap = map

            // Isometric 3D Camera Focus over FTMK Block A
            val initialCam = CameraPosition.Builder()
                .target(LatLng(2.31320, 102.27545))
                .zoom(19.0)
                .tilt(58.0)
                .bearing(25.0)
                .build()
            map.cameraPosition = initialCam

            val emptyStyle = """{"version": 8, "sources": {}, "layers": []}"""
            map.setStyle(Style.Builder().fromJson(emptyStyle)) { style ->
                initMapLayers(style)
            }
        }

        setupFloorSwitcher()
    }

    private fun initMapLayers(style: Style) {
        val geoJson = assets.open("ftmk_map.geojson").use {
            InputStreamReader(it).readText()
        }

        // 1. 3D Rooms Layer
        val roomsSource = GeoJsonSource(ROOMS_SOURCE_ID, geoJson)
        style.addSource(roomsSource)

        val extrusionLayer = FillExtrusionLayer(ROOMS_LAYER_ID, ROOMS_SOURCE_ID).apply {
            setProperties(
                fillExtrusionColor(toColor(get("color"))),
                fillExtrusionHeight(get("height")),
                fillExtrusionBase(get("base_height")),
                fillExtrusionOpacity(0.92f)
            )
            setFilter(eq(get("level"), literal(activeFloor)))
        }
        style.addLayer(extrusionLayer)

        // 2. Navigation Route Line Layer
        val routeSource = GeoJsonSource(ROUTE_SOURCE_ID)
        style.addSource(routeSource)

        val routeLayer = LineLayer(ROUTE_LAYER_ID, ROUTE_SOURCE_ID).apply {
            setProperties(
                lineColor(Color.parseColor("#DC2626")),
                lineWidth(4.5f),
                lineCap(LINE_CAP_ROUND),
                lineJoin(LINE_JOIN_ROUND)
            )
        }
        style.addLayer(routeLayer)

        // 3. Destination Marker Layer (Red Dot)
        val destSource = GeoJsonSource(DEST_SOURCE_ID)
        style.addSource(destSource)

        val destDotLayer = CircleLayer(DEST_LAYER_ID, DEST_SOURCE_ID).apply {
            setProperties(
                circleRadius(9f),
                circleColor(Color.parseColor("#DC2626")),
                circleStrokeWidth(3f),
                circleStrokeColor(Color.WHITE)
            )
        }
        style.addLayer(destDotLayer)
    }

    private fun setupFloorSwitcher() {
        val btnF1: Button = findViewById(R.id.btnFloor1)
        val btnF2: Button = findViewById(R.id.btnFloor2)
        val btnF3: Button = findViewById(R.id.btnFloor3)
        val btnF4: Button = findViewById(R.id.btnFloor4)

        val buttons = listOf(btnF1, btnF2, btnF3, btnF4)

        buttons.forEachIndexed { index, button ->
            val floor = index + 1
            button.setOnClickListener {
                setFloor(floor)
                buttons.forEach { b ->
                    b.setBackgroundColor(Color.TRANSPARENT)
                    b.setTextColor(Color.parseColor("#CBD5E1"))
                }
                button.setBackgroundColor(Color.parseColor("#0284C7"))
                button.setTextColor(Color.WHITE)
            }
        }
    }

    private fun setFloor(floor: Int) {
        activeFloor = floor
        tvFloorBadge.text = "ARAS $floor"
        mapLibreMap?.getStyle { style ->
            val layer = style.getLayer(ROOMS_LAYER_ID) as? FillExtrusionLayer
            layer?.setFilter(eq(get("level"), literal(floor)))
        }
    }

    /**
     * Call this when user selects a destination from directory list or QR scan
     */
    fun navigateToRoom(
        targetRoomId: String,
        roomName: String,
        targetFloor: Int,
        destLatLng: LatLng,
        waypoints: List<LatLng>
    ) {
        if (activeFloor != targetFloor) {
            setFloor(targetFloor)
        }

        tvSelectedTitle.text = roomName
        tvSelectedSubtitle.text = "Floor $targetFloor • Follow highlighted path"

        mapLibreMap?.getStyle { style ->
            // Highlight target room in RED
            val roomLayer = style.getLayer(ROOMS_LAYER_ID) as? FillExtrusionLayer
            roomLayer?.setProperties(
                fillExtrusionColor(
                    switchCase(
                        eq(get("id"), literal(targetRoomId)),
                        color(Color.parseColor("#EF4444")),
                        toColor(get("color"))
                    )
                )
            )

            // Update corridor route line
            val routeSource = style.getSourceAs<GeoJsonSource>(ROUTE_SOURCE_ID)
            val linePoints = waypoints.map { Point.fromLngLat(it.longitude, it.latitude) }
            routeSource?.setGeoJson(LineString.fromLngLats(linePoints))

            // Place Red Dot destination marker exclusively at destination
            val destSource = style.getSourceAs<GeoJsonSource>(DEST_SOURCE_ID)
            val destPoint = Point.fromLngLat(destLatLng.longitude, destLatLng.latitude)
            destSource?.setGeoJson(Feature.fromGeometry(destPoint))

            // Smooth camera transition to target room
            mapLibreMap?.animateCamera(
                CameraUpdateFactory.newLatLngZoom(destLatLng, 19.5),
                1000
            )
        }
    }

    override fun onStart() { super.onStart(); mapView.onStart() }
    override fun onResume() { super.onResume(); mapView.onResume() }
    override fun onPause() { super.onPause(); mapView.onPause() }
    override fun onStop() { super.onStop(); mapView.onStop() }
    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        mapView.onSaveInstanceState(outState)
    }
    override fun onLowMemory() { super.onLowMemory(); mapView.onLowMemory() }
    override fun onDestroy() { super.onDestroy(); mapView.onDestroy() }
}