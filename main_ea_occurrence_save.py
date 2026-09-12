import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

from integracao_ea_khan.ea.occurrence_import_service import OccurrenceImportError, OccurrenceImportService
from integracao_ea_khan.ea.api import TeacherPortalAPI
from integracao_ea_khan.ea.session_manager import SessionManager
from integracao_ea_khan.ea.settings import settings
from integracao_ea_khan.progress import log_progress
from integracao_ea_khan.runtime import user_data_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida ou lanca ocorrencias na EA a partir de um JSON.")
    parser.add_argument("occurrences_file", type=Path)
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("--apply", action="store_true", help="Efetiva os lancamentos. Sem esta opcao, apenas valida a carga.")
    return parser.parse_args()


def build_api(email: str, password: str) -> TeacherPortalAPI:
    account_hash = hashlib.sha256(email.strip().casefold().encode("utf-8")).hexdigest()[:16]
    auth_file = user_data_path("auth", f"ea_auth_{account_hash}.json")
    manager = SessionManager(session=None, auth_file=str(auth_file), email=email, password=password)
    return TeacherPortalAPI(base_url=settings.base_url, session_manager=manager)


def main() -> None:
    args = parse_args()
    with args.occurrences_file.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    OccurrenceImportService.validate_input(payload)
    result = OccurrenceImportService(build_api(args.email, args.password)).import_occurrences(payload, apply=args.apply)
    action = "lancadas" if args.apply else "validadas (dry-run)"
    log_progress("EA", f"{result['student_count']} ocorrencia(s) {action} em {result['class_count']} turma(s).")


if __name__ == "__main__":
    try:
        main()
    except (OccurrenceImportError, OSError, json.JSONDecodeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
