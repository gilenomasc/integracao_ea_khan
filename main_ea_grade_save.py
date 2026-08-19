import argparse
import json
import sys
import traceback
from pathlib import Path

from integracao_ea_khan.ea.api import TeacherPortalAPI
from integracao_ea_khan.ea.grade_import_service import GradeImportError, GradeImportService
from integracao_ea_khan.ea.session_manager import SessionManager
from integracao_ea_khan.ea.settings import settings
from integracao_ea_khan.progress import log_progress


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida ou lanca notas na EA a partir de um JSON.")
    parser.add_argument("grades_file", type=Path)
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("--apply", action="store_true", help="Efetiva o lancamento. Sem esta opcao, apenas valida a carga.")
    return parser.parse_args()


def build_api(email: str, password: str) -> TeacherPortalAPI:
    session_manager = SessionManager(session=None, auth_file=str(settings.auth_file), email=email, password=password)
    return TeacherPortalAPI(base_url=settings.base_url, session_manager=session_manager)


def main() -> None:
    args = parse_args()
    with args.grades_file.open("r", encoding="utf-8") as file:
        grades_payload = json.load(file)
    result = GradeImportService(build_api(args.email, args.password)).import_grades(grades_payload, apply=args.apply)
    action = "lancadas" if args.apply else "validadas (dry-run)"
    log_progress("EA", f"{result['student_count']} notas {action} em {result['class_count']} turmas.")


if __name__ == "__main__":
    try:
        main()
    except (GradeImportError, OSError, json.JSONDecodeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
