"""
Robot Voice Navigation Client
=============================
Demonstrates how a physical robot (e.g. DAMAN Robot or Raspberry Pi / Jetson)
captures voice audio, sends it to the FastAPI backend, and receives navigation directions.
"""

import os
import sys
import requests

BACKEND_URL = "http://localhost:8000/api/v1/assistant/chat/voice"


def send_voice_command(
    audio_path: str,
    session_id: str = "robot_session",
    current_location_id: str = "MAIN_ENTRANCE",
    backend_url: str = BACKEND_URL
):
    """
    Sends a recorded WAV audio file to the AI Guidance Backend.
    
    Returns:
        JSON response with:
        - transcribed_text: What the user said
        - reply: Conversational explanation
        - route_info: Dijkstra shortest route steps (if navigation requested)
        - destination_id: Matched room ID
    """
    if not os.path.exists(audio_path):
        print(f"Error: Audio file '{audio_path}' does not exist.")
        return None

    print(f"🎤 Sending '{audio_path}' to {backend_url}...")

    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {
            "session_id": session_id,
            "current_location_id": current_location_id,
            "language": "en"
        }
        try:
            response = requests.post(backend_url, files=files, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Network error connecting to backend: {e}")
            return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_robot_voice.py <path_to_audio.wav>")
        print("Example: python test_robot_voice.py my_voice.wav")
        sys.exit(1)

    audio_file = sys.argv[1]
    result = send_voice_command(audio_file)

    if result:
        print("\n" + "="*50)
        print("VOICE GUIDANCE RESULT:")
        print("="*50)
        print(f"🗣️ Transcribed Speech: \"{result.get('transcribed_text')}\"")
        print(f"⚡ STT Engine: {result.get('stt_engine')} ({result.get('stt_duration_ms')}ms)")
        print(f"🎯 Target Destination: {result.get('destination_id')}")
        print(f"🤖 Assistant Reply:\n{result.get('reply')}\n")

        route = result.get("route_info")
        if route and route.get("instructions"):
            print("🚶 Route Steps:")
            for i, step in enumerate(route["instructions"], 1):
                print(f"   {i}. {step}")
