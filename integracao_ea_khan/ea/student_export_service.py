import json
from pathlib import Path

from .api import TeacherPortalAPI
from .context_service import get_context_ids_cached


class StudentExportService:
    def __init__(self, api: TeacherPortalAPI):
        self.api = api

    def build_student_payload(self) -> dict[str, dict[str, list[list[str]]]]:
        employee_id, academic_term_id = get_context_ids_cached(
            self.api.session_manager.session,
            test_fn=self.api.test_endpoint,
        )

        turmas = self.api.listar_turmas(employee_id, academic_term_id)
        dados_json = {}

        for turma in turmas:
            nome_turma = turma["CourseOfferingGroup"]
            subterm = self.api.bimestre_atual(turma["SectionSubtermList"])

            if not subterm:
                continue

            print(nome_turma)
            print("-" * 60)

            alunos = self.api.alunos_da_turma(subterm["Identity"])
            dados_json[nome_turma] = {
                "header": ["RA", "Aluno"],
                "rows": [
                    [aluno["AcademicId"], aluno["StudentName"]]
                    for aluno in alunos
                    if aluno["CourseEnrollmentStatus"] == 1
                ],
            }

        return dados_json

    def export_to_json(self, output_file: str) -> dict[str, dict[str, list[list[str]]]]:
        dados_json = self.build_student_payload()
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as arquivo_json:
            json.dump(dados_json, arquivo_json, ensure_ascii=False, indent=2)

        return dados_json
