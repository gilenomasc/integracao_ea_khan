from dataclasses import dataclass
from pathlib import Path
import os

PROJECT_DIR = Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("EA_BASE_URL", "https://7edu-br.educadventista.org")
    auth_file: Path = Path(os.getenv("EA_AUTH_FILE", PROJECT_DIR / "auth" / "ea_auth.json"))

settings = Settings()
