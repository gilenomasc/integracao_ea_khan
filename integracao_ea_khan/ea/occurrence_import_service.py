from __future__ import annotations

import datetime
import json
from copy import deepcopy
from typing import Any

from integracao_ea_khan.progress import log_progress, log_step

from .context_service import get_context_ids_cached
from .api import TeacherPortalAPI


class OccurrenceImportError(ValueError):
    """Indica que uma carga de ocorrencias nao pode ser enviada com seguranca."""


def extract_entity(html: str) -> dict[str, Any]:
    marker = "var entity = eval("
    start = html.find(marker)
    if start == -1:
        raise OccurrenceImportError("Nao encontrei o objeto de ocorrencia retornado pela EA.")
    start += len(marker)
    while start < len(html) and html[start].isspace():
        start += 1
    if start >= len(html) or html[start] != "{":
        raise OccurrenceImportError("A EA retornou um objeto de ocorrencia em formato inesperado.")
    level = 0
    in_string = False
    escape = False
    for index in range(start, len(html)):
        char = html[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            level += 1
        elif char == "}":
            level -= 1
            if level == 0:
                try:
                    return json.loads(html[start:index + 1])
                except json.JSONDecodeError as error:
                    raise OccurrenceImportError("A EA retornou JSON invalido ao criar a ocorrencia.") from error
    raise OccurrenceImportError("Nao encontrei o final do objeto de ocorrencia retornado pela EA.")


class OccurrenceImportService:
    def __init__(self, api: TeacherPortalAPI) -> None:
        self.api = api

    def import_occurrences(self, payload: dict[str, Any], apply: bool = False) -> dict[str, Any]:
        occurrence, classes, options = self.validate_input(payload)
        log_progress("EA", "Validando carga de ocorrencias e consultando turmas atuais.")
        current_classes = self._get_current_classes()
        occurrence_type = self._get_occurrence_type(occurrence["Type"])
        first = current_classes.get(classes[0]["CourseOfferingGroup"])
        if first is None:
            raise OccurrenceImportError(f"Turma {classes[0]['CourseOfferingGroup']!r} nao encontrada entre as turmas ativas da EA.")
        template = extract_entity(self.api.class_occurrence_create(first["section_id"]).text)
        prepared = [self._prepare_class(item, current_classes, template, occurrence, occurrence_type, options) for item in classes]

        results = []
        for index, item in enumerate(prepared, start=1):
            saved = False
            if apply:
                log_step("EA", index, len(prepared), f"Turma {item['class_name']}: lancando para {item['student_count']} aluno(s).")
                self.api.class_occurrence_save(item["save_payload"])
                saved = True
            else:
                log_step("EA", index, len(prepared), f"Turma {item['class_name']}: {item['student_count']} aluno(s) validado(s).")
            results.append({"class_name": item["class_name"], "student_count": item["student_count"], "saved": saved})
        return {"dry_run": not apply, "class_count": len(results), "student_count": sum(item["student_count"] for item in results), "classes": results}

    def _get_current_classes(self) -> dict[str, dict[str, Any]]:
        employee_id, academic_term_id = get_context_ids_cached(self.api.session_manager.session, test_fn=self.api.test_endpoint)
        classes: dict[str, dict[str, Any]] = {}
        for item in self.api.listar_turmas(employee_id, academic_term_id):
            name = item.get("CourseOfferingGroup")
            if not name or name in classes:
                raise OccurrenceImportError(f"A EA retornou uma turma invalida ou repetida: {name!r}.")
            values = {"section_id": item.get("Identity"), "term_course_offering_group_id": item.get("TermCourseOfferingGroupId")}
            if not all(values.values()):
                raise OccurrenceImportError(f"A EA retornou dados incompletos para a turma {name!r}.")
            classes[name] = values
        return classes

    def _get_occurrence_type(self, code: Any) -> dict[str, Any]:
        for item in self.api.load_occurrence_type_list().get("Items", []):
            if item.get("Code") == str(code):
                return item
        raise OccurrenceImportError(f"Tipo de ocorrencia {code!r} nao encontrado ou indisponivel na EA.")

    def _prepare_class(self, class_input: dict[str, Any], current_classes: dict[str, dict[str, Any]], template: dict[str, Any], occurrence: dict[str, Any], occurrence_type: dict[str, Any], options: dict[str, bool]) -> dict[str, Any]:
        class_name = class_input["CourseOfferingGroup"]
        details = current_classes.get(class_name)
        if details is None:
            raise OccurrenceImportError(f"Turma {class_name!r} nao encontrada entre as turmas ativas da EA.")
        students = self.api.load_students_by_section(details["section_id"]).json().get("Data", [])
        requested_ids = [int(ra) for ra in class_input["StudentList"]]
        selected = [student for student in students if int(student["AcademicId"]) in requested_ids]
        if len(selected) != len(requested_ids):
            raise OccurrenceImportError(f"Turma {class_name!r}: um ou mais alunos enviados pelo Excel nao foram encontrados.")

        entity = deepcopy(template)
        entity["Occurrence"].pop("VisualizationDate", None)
        occurrence_date = occurrence.get("OccurrenceDate") or datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        entity["Occurrence"].update({"Type": occurrence_type, "OccurrenceDate": occurrence_date, "Description": occurrence["Description"], "RequiredResponsibleConfirmation": options["required_responsible_confirmation"], "SendNotify": options["send_notify"], "AllowDisplayStudentPortal": options["allow_display_student_portal"], "TermCourseOfferingGroup": {"Identity": details["term_course_offering_group_id"]}, "CourseOfferingSection": {"Identity": details["section_id"]}})
        for student in selected:
            student["OccurrenceDate"] = None
        return {"class_name": class_name, "student_count": len(selected), "save_payload": {"occurrenceForTeacherPortal": {**entity, "StudentList": selected}, "selectedDeliberativeRecomendationIds": [], "isSendLegalSponsor": options["send_legal_sponsor"], "isSendMother": options["send_mother"], "isSendFather": options["send_father"]}}

    @staticmethod
    def validate_input(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, bool]]:
        if not isinstance(payload, dict) or not isinstance(payload.get("InfoTurmas"), list) or not payload["InfoTurmas"]:
            raise OccurrenceImportError("O JSON deve conter uma lista nao vazia em 'InfoTurmas'.")
        occurrence = payload.get("Occurrence")
        if not isinstance(occurrence, dict) or not occurrence.get("Type") or not isinstance(occurrence.get("Description"), str):
            raise OccurrenceImportError("O JSON deve conter 'Occurrence.Type' e 'Occurrence.Description'.")
        class_names = set()
        for item in payload["InfoTurmas"]:
            if not isinstance(item, dict) or not isinstance(item.get("CourseOfferingGroup"), str) or not isinstance(item.get("StudentList"), list) or not item["StudentList"]:
                raise OccurrenceImportError("Cada turma deve ter 'CourseOfferingGroup' e uma lista nao vazia em 'StudentList'.")
            if item["CourseOfferingGroup"] in class_names:
                raise OccurrenceImportError(f"Turma repetida na carga: {item['CourseOfferingGroup']!r}.")
            class_names.add(item["CourseOfferingGroup"])
        raw_options = payload.get("NotificationOptions", {})
        if not isinstance(raw_options, dict):
            raise OccurrenceImportError("'NotificationOptions' deve ser um objeto, quando informado.")
        defaults = {"required_responsible_confirmation": True, "send_notify": True, "allow_display_student_portal": True, "send_legal_sponsor": True, "send_mother": False, "send_father": False}
        options = {key: raw_options.get(key, default) for key, default in defaults.items()}
        if not all(isinstance(value, bool) for value in options.values()):
            raise OccurrenceImportError("Todos os valores de 'NotificationOptions' devem ser booleanos.")
        return occurrence, payload["InfoTurmas"], options
