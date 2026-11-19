import sys
from pathlib import Path
import uvicorn
import webbrowser

# Set up paths
ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "module_1_back_end"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    print("Starting Module 1 Backend on http://127.0.0.1:8000 (accessible on 0.0.0.0:8000) ...")
    webbrowser.open("http://127.0.0.1:8000/docs")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(BACKEND_DIR))