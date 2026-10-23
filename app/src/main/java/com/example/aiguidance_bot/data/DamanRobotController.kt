package com.example.aiguidance_bot.data

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Controller for the DAMAN physical robot.
 *
 * Sends movement commands to the DAMAN BridgeServer via HTTP POST.
 * The BridgeServer must be running on the robot at [baseUrl] (default port 8088).
 *
 * Usage:
 *     val robot = DamanRobotController("http://192.168.1.50:8088")
 *     robot.forward(20) { success, msg -> ... }
 */
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

    /**
     * Execute a full route — a list of movement steps — sequentially.
     * Each step is a map with keys: command, amount, speed (optional).
     *
     * Example route:
     *   listOf(
     *       mapOf("command" to "forward", "amount" to 20),
     *       mapOf("command" to "left",    "amount" to 90),
     *       mapOf("command" to "forward", "amount" to 30),
     *       mapOf("command" to "stop",    "amount" to 0)
     *   )
     */
    fun executeRoute(
        steps: List<Map<String, Any>>,
        onStepComplete: (Int, Boolean, String) -> Unit = { _, _, _ -> },
        onRouteComplete: (Boolean) -> Unit = { _ -> }
    ) {
        Thread {
            var allSuccess = true
            for ((index, step) in steps.withIndex()) {
                val command = step["command"] as? String ?: continue
                val amount = (step["amount"] as? Number)?.toInt() ?: 0
                val speed = (step["speed"] as? Number)?.toInt() ?: defaultSpeed

                var stepSuccess = false
                var stepMessage = ""

                // Use a latch-style synchronous call within this background thread
                val latch = java.util.concurrent.CountDownLatch(1)
                sendMovement(command, amount, speed) { success, message ->
                    stepSuccess = success
                    stepMessage = message
                    latch.countDown()
                }
                latch.await(10, java.util.concurrent.TimeUnit.SECONDS)

                onStepComplete(index, stepSuccess, stepMessage)

                if (!stepSuccess) {
                    allSuccess = false
                    break
                }

                // Small delay between steps to let the robot complete the movement
                if (command != "stop") {
                    Thread.sleep(1500)
                }
            }
            onRouteComplete(allSuccess)
        }.start()
    }

    /**
     * Check if the robot BridgeServer is reachable.
     */
    fun checkConnection(callback: (Boolean, String) -> Unit) {
        Thread {
            try {
                val connection = URL("$baseUrl/manual/base")
                    .openConnection() as HttpURLConnection
                connection.requestMethod = "GET"
                connection.connectTimeout = 3000
                connection.readTimeout = 3000

                val code = connection.responseCode
                callback(code in 200..299, "Robot reachable (HTTP $code)")
                connection.disconnect()
            } catch (e: Exception) {
                callback(false, "Robot unreachable: ${e.message}")
            }
        }.start()
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
