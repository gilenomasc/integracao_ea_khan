from __future__ import annotations

from copy import deepcopy
from math import isfinite
from typing import Any

from integracao_ea_khan.progress import log_progress, log_step

from .api import TeacherPortalAPI
from .context_service import get_context_ids_cached


class GradeImportError(ValueError):
    """Indica que a carga de notas nao pode ser enviada com seguranca."""


def _academic_id_key(value: Any) -> str:
    """Normaliza RAs numericos, inclusive quando o Grid os devolve com zeros a esquerda."""
    if value is None or isinstance(value, bool):
        raise GradeImportError("AcademicId ausente ou invalido.")
    key = str(value).strip()
    if not key:
        raise GradeImportError("AcademicId ausente ou invalido.")
    if key.isdigit():
        return key.lstrip("0") or "0"
    return key


def _class_name_key(value: str) -> str:
    return value.strip().casefold()


class GradeImportService:
    def __init__(self, api: TeacherPortalAPI):
        self.api = api

    def prepare(self, grades_payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Monta e valida todas as cargas antes de persistir qualquer nota."""
        grade_classes = self._validate_input(grades_payload)
        classes_by_name = self._get_current_classes_by_name()
        prepared_classes = []

        for index, grade_class in enumerate(grade_classes, start=1):
            class_name = grade_class["Nome"]
            school_class = classes_by_name.get(_class_name_key(class_name))
            if school_class is None:
                raise GradeImportError(f"Turma {class_name!r} nao encontrada entre as turmas ativas da EA.")

            subterm = self.api.bimestre_atual(school_class["SectionSubtermList"])
            if not subterm:
                raise GradeImportError(f"Turma {class_name!r} nao possui bimestre ativo.")

            class_assignment_id = self.api.get_class_assignment_id(subterm["Identity"])
            if not class_assignment_id:
                raise GradeImportError(f"Turma {class_name!r} nao possui avaliacao cadastrada no bimestre ativo.")

            log_step("EA", index, len(grade_classes), f"Turma {class_name}: lendo dados da avaliacao.")
            grid_rows = self.api.get_student_grades(class_assignment_id)
            save_payload = self._build_save_payload(class_name, grade_class["Notas"], grid_rows)
            prepared_classes.append(
                {
                    "class_name": class_name,
                    "class_assignment_id": class_assignment_id,
                    "save_payload": save_payload,
                }
            )

        return prepared_classes

    def import_grades(self, grades_payload: dict[str, Any], apply: bool = False) -> dict[str, Any]:
        """Valida a carga; com apply=True, envia uma requisicao Save por turma."""
        log_progress("EA", "Validando carga de notas e consultando avaliacoes atuais.")
        prepared_classes = self.prepare(grades_payload)
        result_classes = []

        for index, prepared in enumerate(prepared_classes, start=1):
            class_name = prepared["class_name"]
            student_count = len(prepared["save_payload"])
            class_result = {
                "class_name": class_name,
                "class_assignment_id": prepared["class_assignment_id"],
                "student_count": student_count,
                "saved": False,
            }
            if apply:
                log_step("EA", index, len(prepared_classes), f"Turma {class_name}: lancando {student_count} notas.")
                response = self.api.grade_save(prepared["save_payload"])
                if not 200 <= response.status_code < 300:
                    raise RuntimeError(
                        f"Falha ao salvar notas da turma {class_name!r}: HTTP {response.status_code}. {response.text[:500]}"
                    )
                class_result["saved"] = True
            result_classes.append(class_result)

        return {
            "dry_run": not apply,
            "class_count": len(result_classes),
            "student_count": sum(item["student_count"] for item in result_classes),
            "classes": result_classes,
        }

    def _get_current_classes_by_name(self) -> dict[str, dict[str, Any]]:
        employee_id, academic_term_id = get_context_ids_cached(
            self.api.session_manager.session,
            test_fn=self.api.test_endpoint,
        )
        school_classes = self.api.listar_turmas(employee_id, academic_term_id)
        classes_by_name: dict[str, dict[str, Any]] = {}
        for school_class in school_classes:
            class_name = school_class["CourseOfferingGroup"]
            class_key = _class_name_key(class_name)
            if class_key in classes_by_name:
                raise GradeImportError(f"A EA retornou mais de uma turma com o nome {class_name!r}.")
            classes_by_name[class_key] = school_class
        return classes_by_name

    @staticmethod
    def _validate_input(grades_payload: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(grades_payload, dict) or not isinstance(grades_payload.get("Turmas"), list):
            raise GradeImportError("O JSON de notas deve conter uma lista no campo 'Turmas'.")
        if not grades_payload["Turmas"]:
            raise GradeImportError("O JSON de notas nao contem turmas.")

        seen_classes = set()
        for grade_class in grades_payload["Turmas"]:
            if not isinstance(grade_class, dict) or not isinstance(grade_class.get("Nome"), str):
                raise GradeImportError("Cada turma deve possuir o campo textual 'Nome'.")
            class_key = _class_name_key(grade_class["Nome"])
            if not class_key:
                raise GradeImportError("Cada turma deve possuir um campo 'Nome' nao vazio.")
            if class_key in seen_classes:
                raise GradeImportError(f"Turma repetida na carga: {grade_class['Nome']!r}.")
            seen_classes.add(class_key)
            if not isinstance(grade_class.get("Notas"), list):
                raise GradeImportError(f"Turma {grade_class['Nome']!r} sem lista 'Notas'.")
            if not grade_class["Notas"]:
                raise GradeImportError(f"Turma {grade_class['Nome']!r} sem notas para lancar.")
        return grades_payload["Turmas"]

    @staticmethod
    def _build_save_payload(class_name: str, grades: list[dict[str, Any]], grid_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grid_by_academic_id: dict[str, dict[str, Any]] = {}
        for grid_row in grid_rows:
            key = _academic_id_key(grid_row.get("AcademicId"))
            if key in grid_by_academic_id:
                raise GradeImportError(f"Turma {class_name!r}: AcademicId duplicado no Grid_Read: {key!r}.")
            grid_by_academic_id[key] = grid_row

        save_payload = []
        seen_grades = set()
        for grade in grades:
            if not isinstance(grade, dict):
                raise GradeImportError(f"Turma {class_name!r}: nota invalida.")
            key = _academic_id_key(grade.get("AcademicId"))
            if key in seen_grades:
                raise GradeImportError(f"Turma {class_name!r}: AcademicId repetido na carga: {key!r}.")
            seen_grades.add(key)
            score = grade.get("Score")
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not isfinite(score):
                raise GradeImportError(f"Turma {class_name!r}, AcademicId {key!r}: Score deve ser um numero finito.")
            grid_row = grid_by_academic_id.get(key)
            if grid_row is None:
                raise GradeImportError(f"Turma {class_name!r}: AcademicId {key!r} nao encontrado no Grid_Read.")
            save_row = deepcopy(grid_row)
            save_row["Score"] = score
            save_payload.append(save_row)
        return save_payload
