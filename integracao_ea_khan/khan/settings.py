from dataclasses import dataclass
from pathlib import Path
import os

from integracao_ea_khan.runtime import user_data_path


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("KHAN_BASE_URL", "https://khanacademy.org")
    auth_file: Path = Path(os.getenv("KHAN_AUTH_FILE", user_data_path("auth", "khan_auth.json")))

settings = Settings()
