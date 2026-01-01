# backend/core/settings.py
from pathlib import Path

# .../Online_store/backend
BASE_DIR = Path(__file__).resolve().parents[1]

# .../Online_store/backend/uploads
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
