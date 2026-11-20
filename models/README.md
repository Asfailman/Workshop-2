# AI Speech Models Directory (`models/`)

This directory holds the quantized Whisper.cpp binary model files (`*.bin`) used by the Speech-to-Text (STT) engine for the FTMK Campus Guidance Bot.

> [!NOTE]  
> **Why are `.bin` files not in this Git repository?**  
> GitHub imposes a strict **100 MB per-file limit**. Model weights like `ggml-base.bin` (~148 MB) and `ggml-large-v3-turbo-q5_0.bin` (~574 MB) exceed GitHub's limits and are intentionally excluded in `.gitignore`.

---

## 🚀 Quick Setup for Groupmates

You do **NOT** need to train or compile any models. You can download the pre-quantized models in one command:

### 1. Fast Download (Recommended)
From the project root directory, run:
```bash
python download_models.py
```
This downloads `ggml-base.bin` (~148 MB), which offers ultra-fast (~1 second) transcription for interactive voice chat.

### 2. High-Accuracy Turbo Model (Optional)
If you want the high-accuracy large model for longer speech:
```bash
python download_models.py --all
```

---

## 🌐 Manual Download Links

If you prefer to download manually using your browser or a download manager:

| Model | File Name | Size | Direct Download Link |
| :--- | :--- | :--- | :--- |
| **Whisper Base** *(Fast, ~1s)* | `ggml-base.bin` | ~148 MB | [Download from HuggingFace](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin) |
| **Whisper Large V3 Turbo** *(Heavy)* | `ggml-large-v3-turbo-q5_0.bin` | ~574 MB | [Download from HuggingFace](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin) |

After downloading, place the `.bin` files directly into this `models/` directory.
