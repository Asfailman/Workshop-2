package com.example.damanproject

import android.os.Bundle
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class MainActivityExample : AppCompatActivity() {

    // CHANGE ONLY THIS IP to the DAMAN robot/bridge IP.
    private val robot = DamanRobotController(
        baseUrl = "http://192.168.1.50:8088"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        findViewById<Button>(R.id.btnForward).setOnClickListener {
            robot.forward(20, ::showResult)
        }

        findViewById<Button>(R.id.btnBackward).setOnClickListener {
            robot.backward(20, ::showResult)
        }

        findViewById<Button>(R.id.btnLeft).setOnClickListener {
            robot.left(90, ::showResult)
        }

        findViewById<Button>(R.id.btnRight).setOnClickListener {
            robot.right(90, ::showResult)
        }

        findViewById<Button>(R.id.btnStop).setOnClickListener {
            robot.stop(::showResult)
        }
    }

    private fun showResult(success: Boolean, message: String) {
        runOnUiThread {
            Toast.makeText(
                this,
                if (success) "Robot command sent" else "Error: $message",
                Toast.LENGTH_SHORT
            ).show()
        }
    }
}
