from dataclasses import dataclass
from pathlib import Path
import os

from integracao_ea_khan.runtime import user_data_path


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("EA_BASE_URL", "https://7edu-br.educadventista.org")
    auth_file: Path = Path(os.getenv("EA_AUTH_FILE", user_data_path("auth", "ea_auth.json")))

settings = Settings()
