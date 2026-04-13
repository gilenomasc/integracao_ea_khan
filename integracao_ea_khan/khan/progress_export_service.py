from __future__ import annotations

from datetime import datetime
from pathlib import Path

from integracao_ea_khan.integration.unified_export_service import load_json_file, write_json_file
from integracao_ea_khan.progress import log_progress, log_step


def slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value).strip("_")


def _normalize_lookup_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _extract_profile_handle(profile_root: str | None) -> str | None:
    if not profile_root:
        return None
    cleaned = profile_root.strip().strip("/")
    if not cleaned:
        return None
    parts = cleaned.split("/")
    return parts[-1] if parts else None


def _calculate_grade(best_score: dict | None) -> float | None:
    if not best_score:
        return None
    num_attempted = best_score.get("numAttempted")
    num_correct = best_score.get("numCorrect")
    if not num_attempted or num_correct is None:
        return None
    return round((num_correct / num_attempted) * 100, 2)


class KhanProgressExportService:
    def __init__(self, api) -> None:
        self.api = api

    def _build_student_name_resolver(self, class_payload: dict) -> dict[str, str]:
        resolved_names: dict[str, str] = {}
        roster_file = class_payload.get("rosterFile")
        if not roster_file:
            return resolved_names

        roster_payload = load_json_file(roster_file)
        students = roster_payload.get("students", [])

        for student in students:
            kaid = student.get("kaid")
            if not kaid:
                continue
            resolved_names[kaid] = (
                student.get("coachNickname")
                or student.get("username")
                or _extract_profile_handle(student.get("profileRoot"))
                or kaid
            )

        return resolved_names

    def _build_simplified_class_payload(self, class_name: str, class_payload: dict, progress_payload: dict) -> dict:
        classroom = progress_payload.get("data", {}).get("classroom", {})
        assignments = classroom.get("assignmentsPage", {}).get("assignments", [])
        student_names = self._build_student_name_resolver(class_payload)
        fallback_names = {
            student.get("id"): student.get("coachNickname")
            for student in classroom.get("studentKaidsAndNicknames", [])
            if student.get("id")
        }

        activities = []
        for assignment in assignments:
            contents = assignment.get("contents", [])
            content_title = contents[0].get("translatedTitle") if contents else None
            students = []
            for item_state in assignment.get("itemCompletionStates", []):
                kaid = item_state.get("studentKaid") or item_state.get("student", {}).get("kaid")
                best_score = item_state.get("bestScore")
                students.append(
                    {
                        "kaid": kaid,
                        "name": student_names.get(kaid) or fallback_names.get(kaid) or kaid,
                        "grade": _calculate_grade(best_score),
                        "numCorrect": best_score.get("numCorrect") if best_score else None,
                        "numAttempted": best_score.get("numAttempted") if best_score else None,
                        "state": item_state.get("state"),
                    }
                )

            activities.append(
                {
                    "assignmentId": assignment.get("id"),
                    "assignmentTitle": assignment.get("title"),
                    "contentTitle": content_title,
                    "dueDate": assignment.get("dueDate"),
                    "students": students,
                }
            )

        return {
            "className": class_name,
            "signupCode": class_payload.get("signupCode"),
            "descriptor": class_payload.get("descriptor"),
            "activities": activities,
        }

    def export_from_unified_file(
        self,
        unified_file: str | Path,
        output_dir: str | Path,
        index_output_file: str | Path | None = None,
        simplified_output_file: str | Path | None = None,
        page_size: int = 40,
    ) -> dict:
        unified_path = Path(unified_file)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        log_progress("PROGRESS", f"Carregando consolidado enriquecido de {unified_path}.")
        unified_payload = load_json_file(unified_path)
        classes = unified_payload.get("classes", {})
        total_classes = len(classes)
        exported_classes: dict[str, dict] = {}
        skipped_classes: list[dict] = []
        simplified_classes: dict[str, dict] = {}

        for index, (class_name, class_payload) in enumerate(sorted(classes.items()), start=1):
            descriptor = class_payload.get("descriptor")
            signup_code = class_payload.get("signupCode")
            if not descriptor:
                log_step("PROGRESS", index, total_classes, f"Turma {class_name}: sem descriptor, ignorada.")
                skipped_classes.append(
                    {
                        "className": class_name,
                        "reason": "missing_descriptor",
                    }
                )
                continue

            log_step("PROGRESS", index, total_classes, f"Turma {class_name}: baixando progresso raw.")
            progress_payload = self.api.get_progress_by_student_all_pages(
                class_descriptor=descriptor,
                class_name=class_name,
                page_size=page_size,
            )

            file_path = output_path / f"{slugify(class_name)}_{signup_code or 'sem_codigo'}_progress.json"
            write_json_file(file_path, progress_payload)
            assignment_count = len(
                progress_payload.get("data", {})
                .get("classroom", {})
                .get("assignmentsPage", {})
                .get("assignments", [])
            )
            exported_classes[class_name] = {
                "className": class_name,
                "descriptor": descriptor,
                "signupCode": signup_code,
                "teacherKaid": class_payload.get("teacherKaid"),
                "progressFile": str(file_path),
                "assignmentCount": assignment_count,
            }
            simplified_classes[class_name] = self._build_simplified_class_payload(class_name, class_payload, progress_payload)
            log_progress("PROGRESS", f"Turma {class_name}: progresso raw salvo em {file_path}.")

        manifest = {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "sourceUnifiedFile": str(unified_path),
            "classCount": total_classes,
            "exportedCount": len(exported_classes),
            "skippedCount": len(skipped_classes),
            "classes": exported_classes,
            "skipped": skipped_classes,
        }

        if index_output_file is not None:
            index_path = Path(index_output_file)
            write_json_file(index_path, manifest)
            log_progress("PROGRESS", f"Indice de progresso salvo em {index_path}.")

        if simplified_output_file is not None:
            simplified_path = Path(simplified_output_file)
            simplified_payload = {
                "generatedAt": datetime.now().isoformat(timespec="seconds"),
                "sourceUnifiedFile": str(unified_path),
                "classCount": len(simplified_classes),
                "classes": simplified_classes,
            }
            write_json_file(simplified_path, simplified_payload)
            log_progress("PROGRESS", f"JSON simplificado salvo em {simplified_path}.")

        return manifest
