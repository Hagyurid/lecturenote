import os
from pathlib import Path

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/lecture_actions.sqlite3")
ACTION_API_KEY = os.getenv("ACTION_API_KEY", "")

Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
