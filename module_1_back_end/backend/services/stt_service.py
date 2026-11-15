import importlib
import io
import os
import tempfile
import time
from typing import Dict, Any, Optional

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    whisper = importlib.import_module("whisper")
except Exception:
    whisper = None

try:
    vosk = importlib.import_module("vosk")
except Exception:
    vosk = None

# Import CampusNLP preprocessor & entity resolver
try:
    from AI.campus_nlp import CampusNLP
except ImportError:
    try:
        CampusNLP = getattr(importlib.import_module("campus_nlp"), "CampusNLP", None)
    except Exception:
        CampusNLP = None


CAMPUS_INITIAL_PROMPT = (
    "UTeM, FTMK, Bilik Kuliah, BK 1, BK 2, BK 3, BK 4, BK 5, BK 6, BK 7, BK 8, BK 9, BK 10, "
    "Dewan Kuliah, DK, Makmal AI 1, Makmal AI 2, Makmal AI 3, Makmal AI 4, Programming Lab 1, "
    "Programming Lab 2, Makmal Pengaturcaraan, Makmal Multimedia, Software Engineering Lab, "
    "Database Lab, C-ACT, Students Common Room, Bilik Seminar, Bilik Viva, Main Entrance."
)


class STTService:
    """
    Speech-To-Text (STT) Service for AI Guidance Bot and Physical Robot.
    Supports:
    1. Local OpenAI Whisper models (offline, high accuracy, e.g. 'base', 'tiny')
    2. Google Speech Recognition API fallback (zero GPU/RAM, high accuracy, supports English & Malay)
    """

    def __init__(self, model_size: str = "base", default_language: str = "en"):
        self.model_size = model_size
        self.default_language = default_language
        self._whisper_model = None
        self._recognizer = sr.Recognizer() if sr else None

    def _get_whisper_model(self):
        """Lazy-load Whisper model only when requested."""
        if self._whisper_model is None and whisper is not None:
            try:
                self._whisper_model = whisper.load_model(self.model_size)
            except Exception as e:
                print(f"[STTService] Warning: Failed to load local Whisper model ({e}). Will use fallback.")
                self._whisper_model = False
        return self._whisper_model if self._whisper_model is not False else None

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = None,
        prefer_local: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribes speech audio bytes into text.
        Returns:
            {
                "text": str,
                "engine": "whisper" | "google",
                "duration_ms": float,
                "language": str,
                "success": bool,
                "error": Optional[str]
            }
        """
        start_time = time.time()
        lang = language or self.default_language

        if not audio_bytes or len(audio_bytes) < 100:
            return {
                "text": "",
                "engine": "none",
                "duration_ms": 0.0,
                "language": lang,
                "success": False,
                "error": "Empty or invalid audio data received"
            }

        # Save audio bytes to a temporary file
        suffix = os.path.splitext(filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(audio_bytes)

        try:
            # 1. Try Local Whisper if preferred and available
            if prefer_local:
                model = self._get_whisper_model()
                if model:
                    try:
                        result = model.transcribe(
                            tmp_path,
                            initial_prompt=CAMPUS_INITIAL_PROMPT,
                            language=lang if lang != "auto" else None
                        )
                        text = result.get("text", "").strip()
                        if CampusNLP and text:
                            text = CampusNLP.correct_speech_transcript(text)
                        elapsed = round((time.time() - start_time) * 1000, 2)
                        return {
                            "text": text,
                            "engine": f"whisper-{self.model_size}",
                            "duration_ms": elapsed,
                            "language": lang,
                            "success": True,
                            "error": None
                        }
                    except Exception as e:
                        print(f"[STTService] Whisper transcription error ({e}), falling back...")

            # 2. Fallback to SpeechRecognition (Google Web Speech API)
            if self._recognizer and sr:
                try:
                    with sr.AudioFile(tmp_path) as source:
                        audio_data = self._recognizer.record(source)
                    # Recognize with language hint (e.g. en-US or en-MY)
                    target_lang = "en-US" if lang.startswith("en") else ("ms-MY" if lang.startswith("ms") else lang)
                    text = self._recognizer.recognize_google(audio_data, language=target_lang).strip()
                    if CampusNLP and text:
                        text = CampusNLP.correct_speech_transcript(text)
                    elapsed = round((time.time() - start_time) * 1000, 2)
                    return {
                        "text": text,
                        "engine": "google-speech-api",
                        "duration_ms": elapsed,
                        "language": target_lang,
                        "success": True,
                        "error": None
                    }
                except sr.UnknownValueError:
                    elapsed = round((time.time() - start_time) * 1000, 2)
                    return {
                        "text": "",
                        "engine": "google-speech-api",
                        "duration_ms": elapsed,
                        "language": lang,
                        "success": False,
                        "error": "Could not understand audio (speech unclear or silent)"
                    }
                except Exception as e:
                    elapsed = round((time.time() - start_time) * 1000, 2)
                    return {
                        "text": "",
                        "engine": "google-speech-api",
                        "duration_ms": elapsed,
                        "language": lang,
                        "success": False,
                        "error": str(e)
                    }

            elapsed = round((time.time() - start_time) * 1000, 2)
            return {
                "text": "",
                "engine": "none",
                "duration_ms": elapsed,
                "language": lang,
                "success": False,
                "error": "No speech recognition backend available"
            }

        finally:
            # Clean up temporary audio file
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass


stt_service = STTService()
