package com.example.damanproject

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class DamanRobotController(
    private val baseUrl: String,
    private val defaultSpeed: Int = 200
) {

    fun forward(distanceCm: Int, callback: (Boolean, String) -> Unit = { _, _ -> }) {
        sendMovement("forward", distanceCm, defaultSpeed, callback)
    }

    fun backward(distanceCm: Int, callback: (Boolean, String) -> Unit = { _, _ -> }) {
        sendMovement("backward", distanceCm, defaultSpeed, callback)
    }

    fun left(angleDegrees: Int, callback: (Boolean, String) -> Unit = { _, _ -> }) {
        sendMovement("left", angleDegrees, defaultSpeed, callback)
    }

    fun right(angleDegrees: Int, callback: (Boolean, String) -> Unit = { _, _ -> }) {
        sendMovement("right", angleDegrees, defaultSpeed, callback)
    }

    fun stop(callback: (Boolean, String) -> Unit = { _, _ -> }) {
        sendMovement("stop", 0, defaultSpeed, callback)
    }

    private fun sendMovement(
        command: String,
        amount: Int,
        speed: Int,
        callback: (Boolean, String) -> Unit
    ) {
        // Keep student inputs inside the same limits used by BridgeServer.kt.
        val safeAmount = when (command) {
            "forward", "backward" -> amount.coerceIn(2, 50)
            "left", "right" -> amount.coerceIn(1, 90)
            else -> 0
        }
        val safeSpeed = speed.coerceIn(1, 600)

        val body = JSONObject()
            .put("command", command)
            .put("amount", safeAmount)
            .put("speed", safeSpeed)

        // Android does not allow network operations on the UI thread.
        Thread {
            try {
                val connection = URL("$baseUrl/manual/base")
                    .openConnection() as HttpURLConnection

                connection.requestMethod = "POST"
                connection.setRequestProperty("Content-Type", "application/json")
                connection.connectTimeout = 3000
                connection.readTimeout = 5000
                connection.doOutput = true

                connection.outputStream.use { output ->
                    output.write(body.toString().toByteArray(Charsets.UTF_8))
                }

                val code = connection.responseCode
                val stream = if (code in 200..299) {
                    connection.inputStream
                } else {
                    connection.errorStream
                }

                val response = stream?.bufferedReader()?.use { it.readText() }
                    ?: "HTTP $code"

                callback(code in 200..299, response)
                connection.disconnect()
            } catch (e: Exception) {
                callback(false, e.message ?: "Robot connection failed")
            }
        }.start()
    }
}
