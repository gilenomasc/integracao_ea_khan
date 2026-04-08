import argparse
import csv
import json
import re
import sys
import traceback
from pathlib import Path

from integracao_ea_khan.khan.api import KhanTeacherPortalAPI
from integracao_ea_khan.khan.session_manager import SessionManager
from integracao_ea_khan.khan.settings import settings
from integracao_ea_khan.matching.name_match_service import match_students


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("--output-file", default="tests/class_list_response.json")
    parser.add_argument("--rosters-dir", default="tests/classroom_rosters")
    parser.add_argument("--etapa-ea-file")
    parser.add_argument("--matches-dir", default="tests/matches")
    parser.add_argument("--match-engine", choices=["baseline", "fast"], default="fast")
    parser.add_argument("--match-min-score", type=float)
    return parser.parse_args()


def build_khan_api(email: str, password: str) -> KhanTeacherPortalAPI:
    session_manager = SessionManager(
        session=None,
        auth_file=str(settings.auth_file),
        email=email,
        password=password,
    )
    return KhanTeacherPortalAPI(base_url=settings.base_url, session_manager=session_manager)


def write_json_file(file_path: Path, data) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def write_csv_file(file_path: Path, results: list[dict]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["RA", "Aluno", "Khan Username", "Khan Nickname", "Score", "Status"])
        for row in results:
            writer.writerow([row["ra"], row["school_name"], row["khan_username"] or "", row["khan_name"] or "", row["score"] if row["score"] is not None else "", row["status"]])


def load_json_file(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def slugify(value: str) -> str:
    normalized = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE).strip().lower()
    return re.sub(r"[-\s]+", "_", normalized)


def build_roster_output_path(rosters_dir: Path, classroom: dict) -> Path:
    return rosters_dir / f"{slugify(classroom['name'])}_{classroom['signupCode']}.json"


def build_match_output_paths(matches_dir: Path, classroom_name: str) -> tuple[Path, Path]:
    file_stem = slugify(classroom_name)
    return matches_dir / f"{file_stem}_matches.json", matches_dir / f"{file_stem}_matches.csv"


def main() -> None:
    args = parse_args()
    api = build_khan_api(args.email, args.password)
    output_file = Path(args.output_file)
    rosters_dir = Path(args.rosters_dir)
    class_list = api.get_class_list_simplified()
    write_json_file(output_file, class_list)
    saved_class_list = load_json_file(output_file)
    roster_payloads = []
    for classroom in saved_class_list:
        if not classroom.get("descriptor") or not classroom.get("teacherKaid") or not classroom.get("signupCode"):
            continue
        roster_data = api.get_classroom_roster(classroom["descriptor"], classroom["teacherKaid"], classroom["signupCode"])
        roster_payload = api.build_classroom_roster_from_class_info(classroom, roster_data)
        write_json_file(build_roster_output_path(rosters_dir, classroom), roster_payload)
        roster_payloads.append(roster_payload)
    if not args.etapa_ea_file:
        return
    etapa_ea_payload = load_json_file(Path(args.etapa_ea_file))
    matches_dir = Path(args.matches_dir)
    for roster_payload in roster_payloads:
        class_name = roster_payload["name"]
        if class_name not in etapa_ea_payload:
            continue
        match_result = match_students(etapa_ea_payload, roster_payload, class_name, min_score=args.match_min_score, engine=args.match_engine)
        json_path, csv_path = build_match_output_paths(matches_dir, class_name)
        write_json_file(json_path, match_result)
        write_csv_file(csv_path, match_result["results"])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
