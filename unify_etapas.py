from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from integracao_ea_khan.integration.unified_export_service import build_unified_payload, load_json_file, load_match_results, write_json_file
from integracao_ea_khan.progress import log_progress


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ea-email", required=True)
    parser.add_argument("--ea-password", required=True)
    parser.add_argument("--khan-email", required=True)
    parser.add_argument("--khan-password", required=True)
    parser.add_argument("--output-dir", default="tests/unified")
    parser.add_argument("--output-json")
    parser.add_argument("--match-engine", choices=["baseline", "fast"], default="fast")
    parser.add_argument("--match-min-score", type=float)
    parser.add_argument("--skip-ea", action="store_true")
    parser.add_argument("--skip-khan", action="store_true")
    return parser.parse_args()


def run_command(command: list[str], workdir: Path) -> None:
    log_progress("UNIFY", f"Executando: {' '.join(command)}")
    subprocess.run(command, cwd=workdir, check=True)


def main() -> None:
    args = parse_args()
    log_progress("UNIFY", "Inicializando pipeline unificado.")
    project_dir = Path(__file__).resolve().parent
    output_dir = (project_dir / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    etapa_ea_json = output_dir / "etapa_ea_alunos.json"
    class_list_json = output_dir / "class_list_response.json"
    rosters_dir = output_dir / "rosters"
    matches_dir = output_dir / "matches"
    unified_json = Path(args.output_json).resolve() if args.output_json else output_dir / "unified_matches.json"

    if not args.skip_ea:
        log_progress("UNIFY", "Etapa 1/3: exportando base EA.")
        run_command([sys.executable, "main_ea.py", str(etapa_ea_json), args.ea_email, args.ea_password], project_dir)
    if not args.skip_khan:
        log_progress("UNIFY", "Etapa 2/3: exportando dados Khan e executando matching.")
        command = [
            sys.executable,
            "main_khan.py",
            args.khan_email,
            args.khan_password,
            "--output-file",
            str(class_list_json),
            "--rosters-dir",
            str(rosters_dir),
            "--etapa-ea-file",
            str(etapa_ea_json),
            "--matches-dir",
            str(matches_dir),
            "--match-engine",
            args.match_engine,
        ]
        if args.match_min_score is not None:
            command.extend(["--match-min-score", str(args.match_min_score)])
        run_command(command, project_dir)

    log_progress("UNIFY", "Etapa 3/3: consolidando JSON unificado.")
    etapa_ea_payload = load_json_file(etapa_ea_json)
    match_results = load_match_results(matches_dir)
    unified_payload = build_unified_payload(etapa_ea_payload, match_results, args.match_engine, etapa_ea_json, rosters_dir, matches_dir)
    write_json_file(unified_json, unified_payload)
    log_progress("UNIFY", f"JSON unificado salvo em: {unified_json}")


if __name__ == "__main__":
    main()
