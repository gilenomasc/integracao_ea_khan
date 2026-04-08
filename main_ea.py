import argparse

from integracao_ea_khan.ea.api import TeacherPortalAPI
from integracao_ea_khan.ea.session_manager import SessionManager
from integracao_ea_khan.ea.settings import settings
from integracao_ea_khan.ea.student_export_service import StudentExportService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_file")
    parser.add_argument("email")
    parser.add_argument("password")
    return parser.parse_args()


def build_api(email: str, password: str) -> TeacherPortalAPI:
    session_manager = SessionManager(
        session=None,
        auth_file=str(settings.auth_file),
        email=email,
        password=password,
    )
    return TeacherPortalAPI(base_url=settings.base_url, session_manager=session_manager)


def main() -> None:
    args = parse_args()
    api = build_api(args.email, args.password)
    export_service = StudentExportService(api)
    data = export_service.export_to_json(args.output_file)
    print(f"JSON gerado com {len(data)} turmas em {args.output_file}")


if __name__ == "__main__":
    main()
