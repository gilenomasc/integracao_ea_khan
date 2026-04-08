from dataclasses import dataclass
from pathlib import Path
import os

PROJECT_DIR = Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("KHAN_BASE_URL", "https://khanacademy.org")
    auth_file: Path = Path(os.getenv("KHAN_AUTH_FILE", PROJECT_DIR / "auth" / "khan_auth.json"))

settings = Settings()
