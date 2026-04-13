from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json


def load_json_file(file_path: str | Path):
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json_file(file_path: str | Path, data) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _build_roster_index(rosters_dir: str | Path) -> dict[str, dict]:
    path = Path(rosters_dir)
    roster_index: dict[str, dict] = {}
    for roster_file in sorted(path.glob("*.json")):
        roster_payload = load_json_file(roster_file)
        class_name = roster_payload.get("name")
        if not class_name:
            continue
        roster_index[class_name] = {
            "descriptor": roster_payload.get("descriptor"),
            "teacherKaid": roster_payload.get("teacherKaid"),
            "signupCode": roster_payload.get("signupCode"),
            "topics": roster_payload.get("topics", []),
            "countStudents": roster_payload.get("countStudents"),
            "rosterFile": str(roster_file),
        }
    return roster_index


def build_unified_payload(
    etapa_ea_payload: dict,
    match_results: list[dict],
    engine: str,
    etapa_ea_file: str | Path,
    rosters_dir: str | Path,
    matches_dir: str | Path,
) -> dict:
    roster_index = _build_roster_index(rosters_dir)
    classes = {
        result["className"]: {
            **result,
            **roster_index.get(result["className"], {}),
        }
        for result in sorted(match_results, key=lambda item: item["className"])
    }

    summary = {
        "classCountEtapaEA": len(etapa_ea_payload),
        "classCountMatched": len(match_results),
        "schoolStudentCount": sum(result["schoolStudentCount"] for result in match_results),
        "khanStudentCount": sum(result["khanStudentCount"] for result in match_results),
        "matchedCount": sum(result["matchedCount"] for result in match_results),
        "warningCount": sum(len(result["warnings"]) for result in match_results),
        "unmatchedKhanCount": sum(len(result["unmatchedKhan"]) for result in match_results),
    }

    return {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "engine": engine,
        "sources": {
            "etapaEAFile": str(Path(etapa_ea_file)),
            "rostersDir": str(Path(rosters_dir)),
            "matchesDir": str(Path(matches_dir)),
        },
        "summary": summary,
        "classes": classes,
    }


def load_match_results(matches_dir: str | Path) -> list[dict]:
    path = Path(matches_dir)
    results = []
    for match_file in sorted(path.glob("*_matches.json")):
        results.append(load_json_file(match_file))
    return results
