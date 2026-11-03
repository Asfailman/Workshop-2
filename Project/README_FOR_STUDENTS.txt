DAMAN ROBOT - SIMPLE STUDENT STARTER
===================================

PROJECT:
AI-Powered Intelligent Guidance and Navigation Application Using an Autonomous Service Robot

RECOMMENDED APPROACH
--------------------
Use Kotlin/Android for the main mobile application.
Python is optional for AI experiments or movement-logic testing.

The provided DAMAN BridgeServer already accepts these movement commands:
- forward
- backward
- left
- right
- stop

Bridge endpoint:
POST http://ROBOT_IP:8088/manual/base

IMPORTANT:
1. The DAMAN robot-side BridgeServer must already be running.
2. The Android phone/computer and robot should be reachable on the same network.
3. Replace 192.168.1.50 with the actual robot/bridge IP address.
4. Do NOT remove or bypass the robot's emergency-stop/safety logic.
5. Test at low speed and in a clear area first.

FILES
-----
1. DamanRobotController.kt
   Main file students should use in the Android project.

2. MainActivityExample.kt
   Shows how Android buttons call the robot functions.

3. activity_main.xml
   Very simple five-button interface.

4. robot_control.py
   Optional Python version for testing or AI/navigation experiments.

ANDROID SETUP
-------------
Put DamanRobotController.kt in:
app/src/main/java/<your_package>/

Put activity_main.xml in:
app/src/main/res/layout/

Add Internet permission to AndroidManifest.xml:

<uses-permission android:name="android.permission.INTERNET" />

For a local HTTP bridge during development, the app may also need:

<application
    android:usesCleartextTraffic="true"
    ... >

STUDENT CODE SHOULD LOOK THIS SIMPLE
------------------------------------
robot.forward(20)
robot.left(90)
robot.forward(30)
robot.right(90)
robot.stop()

PROJECT LOGIC EXAMPLE
---------------------
User says: "Take me to Room 105"
        -> AI understands Room 105
        -> route planner creates route
        -> route is converted to movement commands
        -> DamanRobotController sends commands to robot

Example route:
Forward 20 cm
Left 90 degrees
Forward 30 cm
Right 90 degrees
Forward 20 cm
Stop


