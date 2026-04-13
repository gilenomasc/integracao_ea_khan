from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from integracao_ea_khan.khan.api import KhanTeacherPortalAPI
from integracao_ea_khan.khan.progress_export_service import KhanProgressExportService
from integracao_ea_khan.khan.session_manager import SessionManager
from integracao_ea_khan.khan.settings import settings
from integracao_ea_khan.progress import log_progress


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("--unified-file", default="tests/unified/unified_matches.json")
    parser.add_argument("--output-dir", default="tests/unified/progress_raw")
    parser.add_argument("--index-output-file", default="tests/unified/progress_raw_index.json")
    parser.add_argument("--simplified-output-file", default="tests/unified/progress_simplified.json")
    parser.add_argument("--page-size", type=int, default=40)
    return parser.parse_args()


def build_khan_api(email: str, password: str) -> KhanTeacherPortalAPI:
    session_manager = SessionManager(
        session=None,
        auth_file=str(settings.auth_file),
        email=email,
        password=password,
    )
    return KhanTeacherPortalAPI(base_url=settings.base_url, session_manager=session_manager)


def main() -> None:
    args = parse_args()
    log_progress("PROGRESS", "Inicializando exportacao de progresso Khan.")
    api = build_khan_api(args.email, args.password)
    service = KhanProgressExportService(api)
    manifest = service.export_from_unified_file(
        unified_file=Path(args.unified_file),
        output_dir=Path(args.output_dir),
        index_output_file=Path(args.index_output_file),
        simplified_output_file=Path(args.simplified_output_file),
        page_size=args.page_size,
    )
    log_progress(
        "PROGRESS",
        f"Exportacao concluida: {manifest['exportedCount']} turmas exportadas, {manifest['skippedCount']} ignoradas.",
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
