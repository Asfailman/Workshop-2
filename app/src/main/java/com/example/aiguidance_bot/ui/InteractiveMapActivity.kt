package com.example.aiguidance_bot.ui

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.View
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ImageButton
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.aiguidance_bot.R
import com.example.aiguidance_bot.telemetry.RobotNavigationBridge
import org.json.JSONObject

/**
 * Hosts the hardware-accelerated WebView, injects ftmk_map.geojson from assets,
 * and registers the AndroidBridge JavaScript interface for Robot Telemetry HUD updates.
 */
class InteractiveMapActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var tvDistance: TextView
    private lateinit var tvTime: TextView
    private lateinit var tvWaypoints: TextView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_interactive_map)

        // Initialize UI components
        tvDistance = findViewById(R.id.tvDistance)
        tvTime = findViewById(R.id.tvTime)
        tvWaypoints = findViewById(R.id.tvWaypoints)
        webView = findViewById(R.id.webViewInteractiveMap)

        findViewById<ImageButton>(R.id.btnBack).setOnClickListener { finish() }

        setupWebView()
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        // Hardware acceleration for WebGL / 3D Canvas
        webView.setLayerType(View.LAYER_TYPE_HARDWARE, null)
        
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = true
            cacheMode = WebSettings.LOAD_DEFAULT
            builtInZoomControls = false
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
        }

        // Bridge to receive Navigation Telemetry from HTML and update HUD
        val bridge = RobotNavigationBridge { distanceMeters, estimatedSeconds, waypointsCount ->
            runOnUiThread {
                tvDistance.text = String.format("Distance: %.1f m", distanceMeters)
                tvTime.text = "ETA: $estimatedSeconds sec"
                tvWaypoints.text = "Waypoints: $waypointsCount"
            }
        }
        
        // Inject JS bridge
        webView.addJavascriptInterface(bridge, "AndroidBridge")

        // Intercept page load completion to fire initial intents
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                val targetDestination = intent.getStringExtra("DESTINATION_NAME")
                if (!targetDestination.isNullOrEmpty()) {
                    val escapedDestination = JSONObject.quote(targetDestination)
                    webView.evaluateJavascript("window.navigateToFacilityByName($escapedDestination);", null)
                }
            }
        }
        
        // Load the local HTML file which internally fetches the geojson
        webView.loadUrl("file:///android_asset/ftmk_map.html")
    }

    override fun onDestroy() {
        webView.stopLoading()
        webView.removeJavascriptInterface("AndroidBridge")
        webView.destroy()
        super.onDestroy()
    }
}