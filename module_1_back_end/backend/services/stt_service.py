import glob
import importlib
import io
import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import Dict, Any, Optional, Tuple

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from pywhispercpp.model import Model as WhisperCppModel, ContextParams
except ImportError:
    WhisperCppModel = None
    ContextParams = None

try:
    whisper = importlib.import_module("whisper")
except Exception:
    whisper = None

try:
    vosk = importlib.import_module("vosk")
except Exception:
    vosk = None

try:
    import numpy as np
except ImportError:
    np = None

# Import CampusNLP preprocessor & entity resolver
try:
    from AI.campus_nlp import CampusNLP
except ImportError:
    try:
        CampusNLP = getattr(importlib.import_module("campus_nlp"), "CampusNLP", None)
    except Exception:
        CampusNLP = None


# Bilingual English + Malay campus vocabulary prompt for Whisper language identification & bias
CAMPUS_INITIAL_PROMPT = (
    "UTeM, FTMK, Bilik Kuliah, BK 1, BK 2, BK 3, BK 4, BK 5, BK 6, BK 7, BK 8, BK 9, BK 10, "
    "Dewan Kuliah, DK, Makmal AI 1, Makmal AI 2, Makmal AI 3, Makmal AI 4, Programming Lab 1, "
    "Programming Lab 2, Makmal Pengaturcaraan, Makmal Multimedia, Software Engineering Lab, "
    "Database Lab, C-ACT, Students Common Room, Bilik Seminar, Bilik Viva, Lobi Utama, Main Entrance, "
    "di mana, tunjukkan jalan, tolong bawa saya, nak pergi ke, where is, how to get to, take me to."
)

FILLER_REGEX = re.compile(
    r'\b(?:u+h+m*|u+m+|h+m+|e+r+m*|a+h+|e+h+|e+m+|a+a+)\b|'
    r'\[(?:music|applause|laughter|silence|sigh|cough|groan|bell)\]|'
    r'\((?:music|applause|laughter|silence|sigh|cough|groan|bell)\)',
    re.IGNORECASE
)

NUMBER_WORD_REPLACEMENTS = [
    # Malay compound numbers
    (re.compile(r'\bsebelas\b', re.I), '11'),
    (re.compile(r'\bdua\s*belas\b', re.I), '12'),
    (re.compile(r'\btiga\s*belas\b', re.I), '13'),
    (re.compile(r'\bempat\s*belas\b', re.I), '14'),
    (re.compile(r'\blima\s*belas\b', re.I), '15'),
    (re.compile(r'\benam\s*belas\b', re.I), '16'),
    # English compound numbers
    (re.compile(r'\beleven\b', re.I), '11'),
    (re.compile(r'\btwelve\b', re.I), '12'),
    (re.compile(r'\bthirteen\b', re.I), '13'),
    (re.compile(r'\bfourteen\b', re.I), '14'),
    (re.compile(r'\bfifteen\b', re.I), '15'),
    (re.compile(r'\bsixteen\b', re.I), '16'),
    # Single digits & ordinals
    (re.compile(r'\b(?:zero|sifar|kosong)\b', re.I), '0'),
    (re.compile(r'\b(?:one|first|satu|pertama)\b', re.I), '1'),
    (re.compile(r'\b(?:two|second|dua|kedua)\b', re.I), '2'),
    (re.compile(r'\b(?:three|third|tiga|ketiga)\b', re.I), '3'),
    (re.compile(r'\b(?:four|fourth|empat|keempat)\b', re.I), '4'),
    (re.compile(r'\b(?:five|fifth|lima|kelima)\b', re.I), '5'),
    (re.compile(r'\b(?:six|sixth|enam|keenam)\b', re.I), '6'),
    (re.compile(r'\b(?:seven|seventh|tujuh|ketujuh)\b', re.I), '7'),
    (re.compile(r'\b(?:eight|eighth|lapan|kelapan)\b', re.I), '8'),
    (re.compile(r'\b(?:nine|ninth|sembilan|kesembilan)\b', re.I), '9'),
    (re.compile(r'\b(?:ten|tenth|sepuluh|kesepuluh)\b', re.I), '10'),
]


def clean_vocal_fillers_and_numbers(text: str) -> str:
    """Removes filler noises (uh, um, hmm, er) and converts spoken numbers to digits."""
    if not text:
        return ""
    # 1. Strip fillers
    cleaned = FILLER_REGEX.sub(' ', text)
    cleaned = re.sub(r'[\.\,]+', ' ', cleaned)

    # 2. Convert number words to digits
    for pattern, replacement in NUMBER_WORD_REPLACEMENTS:
        cleaned = pattern.sub(replacement, cleaned)

    return re.sub(r'\s+', ' ', cleaned).strip()


def _ensure_16k_mono_wav(input_wav_path: str, output_wav_path: str) -> Tuple[str, float]:
    """
    Ensures the audio file is 16kHz mono 16-bit PCM and applies auto-gain if audio is quiet.
    Returns (output_file_path, duration_seconds).
    """
    duration_sec = 0.0
    try:
        import wave
        if np is None:
            return input_wav_path, duration_sec

        with wave.open(input_wav_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_bytes = wf.readframes(n_frames)
            duration_sec = n_frames / float(framerate) if framerate > 0 else 0.0

        if sampwidth == 2:
            dtype = np.int16
        elif sampwidth == 1:
            dtype = np.uint8
        elif sampwidth == 4:
            dtype = np.int32
        else:
            return input_wav_path, duration_sec

        audio = np.frombuffer(audio_bytes, dtype=dtype)
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1).astype(dtype)

        # Resample to 16000 if necessary
        if framerate != 16000 and framerate > 0:
            new_length = int(len(audio) * 16000 / framerate)
            audio = np.interp(
                np.linspace(0, len(audio), new_length, endpoint=False),
                np.arange(len(audio)),
                audio
            ).astype(np.int16)
        else:
            audio = audio.astype(np.int16)

        # Auto-Gain: if mic recording is quiet, boost volume so Whisper hears clearly
        max_val = int(np.max(np.abs(audio))) if len(audio) > 0 else 0
        if 0 < max_val < 14000:
            gain = min(4.0, 20000.0 / float(max_val))
            audio = np.clip(audio * gain, -32768, 32767).astype(np.int16)
            print(f"[STTService] Applied Auto-Gain {gain:.2f}x (original peak: {max_val})")

        with wave.open(output_wav_path, "wb") as out_wf:
            out_wf.setnchannels(1)
            out_wf.setsampwidth(2)
            out_wf.setframerate(16000)
            out_wf.writeframes(audio.tobytes())

        return output_wav_path, duration_sec
    except Exception as e:
        print(f"[STTService] Audio normalization note: {e}")
        return input_wav_path, duration_sec


class STTService:
    """
    High-Performance Speech-To-Text (STT) Service with Auto-Language Detection,
    Vocal Filler Suppression, Number Conversion, and Automatic GPU/CPU Load Balancing.
    """

    def __init__(
        self,
        fallback_model_size: str = "base",
        n_threads: Optional[int] = None
    ):
        self.fallback_model_size = fallback_model_size
        self.n_threads = n_threads or min(10, os.cpu_count() or 4)

        # Models in cache / memory
        self._models = {}  # { "base": Model, "turbo": Model }
        self._gpu_available = self._detect_gpu()
        self._recognizer = sr.Recognizer() if sr else None

    def _detect_gpu(self) -> bool:
        """Automatically detects if an active NVIDIA GPU (e.g. RTX 5060) is available."""
        try:
            if shutil.which("nvidia-smi"):
                res = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if res.returncode == 0 and res.stdout.strip():
                    gpu_name = res.stdout.strip().splitlines()[0]
                    print(f"[STTService] GPU Auto-Detected: {gpu_name}")
                    return True
        except Exception:
            pass
        return False

    def _resolve_model_path(self, model_key: str = "base") -> Optional[str]:
        """Finds the model file in the models/ directory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_dirs = [
            os.path.abspath(os.path.join(current_dir, "../../../models")),
            os.path.abspath(os.path.join(current_dir, "../../models")),
            os.path.abspath("models"),
            os.path.abspath("../models"),
        ]

        target_file = "ggml-base.bin" if model_key == "base" else "ggml-large-v3-turbo-q5_0.bin"

        for d in candidate_dirs:
            exact = os.path.join(d, target_file)
            if os.path.exists(exact):
                return exact

        for d in candidate_dirs:
            matches = glob.glob(os.path.join(d, "ggml*.bin"))
            if matches:
                return matches[0]

        return None

    def _get_model(self, model_key: str = "base"):
        """Loads and caches the requested Whisper.cpp model with GPU acceleration if supported."""
        if model_key in self._models:
            return self._models[model_key]

        if WhisperCppModel is None:
            return None

        model_path = self._resolve_model_path(model_key)
        if not model_path or not os.path.exists(model_path):
            return None

        try:
            print(f"[STTService] Initializing model ({model_key}): {os.path.basename(model_path)} (threads={self.n_threads}, GPU={self._gpu_available})...")

            context_params = None
            if self._gpu_available and ContextParams is not None:
                try:
                    context_params = ContextParams(
                        use_gpu=True,
                        flash_attn=True,
                        gpu_device=0
                    )
                except Exception:
                    context_params = None

            model_kwargs = {
                "n_threads": self.n_threads,
                "print_realtime": False,
                "print_progress": False
            }
            if context_params is not None:
                model_kwargs["context_params"] = context_params

            loaded_model = WhisperCppModel(model_path, **model_kwargs)
            self._models[model_key] = loaded_model
            print(f"[STTService] Model ({model_key}) loaded successfully.")
            return loaded_model
        except Exception as e:
            print(f"[STTService] Failed to load model ({model_key}): {e}")
            return None

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = "auto",
        prefer_local: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribes speech audio bytes with:
        - Auto Language Detection (Malay & English)
        - Sub-second execution for interactive queries
        - Automatic Heavy-load offloading for long speech
        - Vocal filler removal ('uhmm', 'hmm', 'uh', 'err')
        - Spoken numbers converted to digits (one/satu -> 1)
        """
        start_time = time.time()

        if not audio_bytes or len(audio_bytes) < 100:
            return {
                "text": "",
                "engine": "none",
                "duration_ms": 0.0,
                "language": language or "auto",
                "success": False,
                "error": "Empty or invalid audio data received"
            }

        suffix = os.path.splitext(filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(audio_bytes)

        conv_path = tmp_path + "_16k.wav"

        try:
            # 1. 16kHz conversion + auto gain boost
            wav_to_transcribe, audio_duration = _ensure_16k_mono_wav(tmp_path, conv_path)

            # 2. Heavy-load Auto Detection:
            # If audio is long (>= 7.0s) or heavy mode is explicitly set, route to Turbo model
            env_mode = os.environ.get("WHISPER_MODEL", "").lower()
            if "turbo" in env_mode or "large" in env_mode or audio_duration >= 7.0:
                model_key = "turbo"
            else:
                model_key = "base"  # Fast ~1s response for standard queries

            raw_text = ""
            engine_used = f"whisper-cpp-ggml-{model_key}"

            # 3. Primary STT: Whisper.cpp
            if prefer_local:
                model = self._get_model(model_key)
                if not model and model_key == "turbo":
                    model = self._get_model("base")
                    model_key = "base"
                    engine_used = "whisper-cpp-ggml-base"

                if model:
                    try:
                        params = {
                            "single_segment": True,
                            "no_timestamps": True,
                            "temperature": 0.0,
                            "n_threads": self.n_threads,
                            "suppress_blank": True,
                        }

                        if language and language.lower() not in ["auto", "", "detect", "none"]:
                            params["language"] = language.split("-")[0].lower()
                        else:
                            params["language"] = ""  # whisper.cpp expects "" for automatic language detection

                        if CAMPUS_INITIAL_PROMPT:
                            params["initial_prompt"] = CAMPUS_INITIAL_PROMPT

                        segments = model.transcribe(wav_to_transcribe, **params)
                        raw_text = " ".join(seg.text for seg in segments).strip()
                        print(f"[STTService] Whisper raw output: '{raw_text}' ({audio_duration:.2f}s audio)")
                    except Exception as e:
                        print(f"[STTService] Whisper.cpp error ({e}), trying fallback...")

            # 4. Fallback to Google Speech Recognition if Whisper detected no words
            if not raw_text and self._recognizer and sr:
                try:
                    with sr.AudioFile(wav_to_transcribe) as source:
                        audio_data = self._recognizer.record(source)
                    target_lang = "ms-MY" if language == "ms" else "en-US"
                    raw_text = self._recognizer.recognize_google(audio_data, language=target_lang).strip()
                    engine_used = "google-speech-fallback"
                    print(f"[STTService] Google Speech fallback transcribed: '{raw_text}'")
                except Exception:
                    pass

            # 5. Clean fillers & convert spoken number words (one/satu -> 1)
            clean_text = clean_vocal_fillers_and_numbers(raw_text)

            # 6. Apply campus entity & phonetic correction
            if CampusNLP and clean_text:
                clean_text = CampusNLP.correct_speech_transcript(clean_text)

            elapsed = round((time.time() - start_time) * 1000, 2)
            detected_lang = language or "auto"

            return {
                "text": clean_text,
                "raw_transcript": raw_text,
                "engine": engine_used,
                "duration_ms": elapsed,
                "language": detected_lang,
                "success": bool(clean_text),
                "error": None if clean_text else "Could not transcribe audio"
            }

        finally:
            for p in (tmp_path, conv_path):
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass


stt_service = STTService()
