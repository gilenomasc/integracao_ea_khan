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


def build_unified_payload(
    etapa_ea_payload: dict,
    match_results: list[dict],
    engine: str,
    etapa_ea_file: str | Path,
    rosters_dir: str | Path,
    matches_dir: str | Path,
) -> dict:
    classes = {
        result["className"]: result
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
