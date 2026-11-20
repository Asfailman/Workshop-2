"""
Speech-to-Text Model Downloader
===============================
Whisper.cpp binary models (ggml-*.bin) exceed GitHub's 100MB file limit
and cannot be pushed to GitHub directly.

This script automatically downloads the models from the official HuggingFace repository:
https://huggingface.co/ggerganov/whisper.cpp

Usage:
    python download_models.py          # Downloads the fast base model (~148 MB, recommended)
    python download_models.py --all    # Downloads both base and large-turbo models (~722 MB)
"""

import os
import sys
import time
import urllib.request

MODELS = {
    "base": {
        "filename": "ggml-base.bin",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
        "size_mb": 148,
        "desc": "Ultra-fast interactive model (~1s latency, recommended for mobile voice chat)"
    },
    "turbo": {
        "filename": "ggml-large-v3-turbo-q5_0.bin",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin",
        "size_mb": 574,
        "desc": "High-accuracy quantized model (best for noisy environments or long speech)"
    }
}


def download_file_with_progress(url: str, dest_path: str, expected_mb: float):
    print(f"\n--> Downloading: {os.path.basename(dest_path)} (~{expected_mb} MB)")
    print(f"    Source: {url}")
    print(f"    Target: {dest_path}")

    start_time = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    temp_path = dest_path + ".tmp"
    try:
        with urllib.request.urlopen(req) as resp, open(temp_path, "wb") as out_file:
            total_bytes = int(resp.headers.get("content-length", expected_mb * 1024 * 1024))
            downloaded = 0
            chunk_size = 1024 * 512  # 512 KB chunks

            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)

                elapsed = max(0.1, time.time() - start_time)
                speed_mb_s = (downloaded / (1024 * 1024)) / elapsed
                percent = min(100.0, (downloaded / total_bytes) * 100) if total_bytes > 0 else 0
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_bytes / (1024 * 1024)

                sys.stdout.write(
                    f"\r    [{percent:5.1f}%] {mb_downloaded:6.1f}MB / {mb_total:6.1f}MB ({speed_mb_s:4.2f} MB/s)"
                )
                sys.stdout.flush()

        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(temp_path, dest_path)
        print(f"\n[OK] Successfully saved to: {dest_path}\n")
        return True
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"\n[Error] Download failed: {e}\n")
        return False


def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(repo_root, "models")
    os.makedirs(models_dir, exist_ok=True)

    download_all = "--all" in sys.argv or "--turbo" in sys.argv
    keys_to_download = ["base", "turbo"] if download_all else ["base"]

    print("=" * 65)
    print("FTMK Campus AI - Whisper.cpp Model Setup")
    print("=" * 65)

    for key in keys_to_download:
        info = MODELS[key]
        dest = os.path.join(models_dir, info["filename"])

        if os.path.exists(dest):
            size_mb = os.path.getsize(dest) / (1024 * 1024)
            print(f"[Already Exists] {info['filename']} ({size_mb:.1f} MB) in models/")
            continue

        print(f"\nModel: {key.upper()} - {info['desc']}")
        success = download_file_with_progress(info["url"], dest, info["size_mb"])
        if not success:
            print(f"Failed to download {info['filename']}. You can download manually from:")
            print(info["url"])

    print("=" * 65)
    print("Model setup complete! You can now start the backend server:")
    print("    python -m uvicorn module_1_back_end.backend.main:app --reload")
    print("=" * 65)


if __name__ == "__main__":
    main()
