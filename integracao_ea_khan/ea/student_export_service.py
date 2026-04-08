import json
from pathlib import Path

from integracao_ea_khan.progress import log_progress, log_step

from .api import TeacherPortalAPI
from .context_service import get_context_ids_cached


class StudentExportService:
    def __init__(self, api: TeacherPortalAPI):
        self.api = api

    def build_student_payload(self) -> dict[str, dict[str, list[list[str]]]]:
        log_progress("EA", "Buscando contexto da sessao.")
        employee_id, academic_term_id = get_context_ids_cached(
            self.api.session_manager.session,
            test_fn=self.api.test_endpoint,
        )

        log_progress("EA", "Listando turmas disponiveis.")
        turmas = self.api.listar_turmas(employee_id, academic_term_id)
        dados_json = {}
        log_progress("EA", f"{len(turmas)} turmas recebidas para analise.")

        for index, turma in enumerate(turmas, start=1):
            nome_turma = turma["CourseOfferingGroup"]
            subterm = self.api.bimestre_atual(turma["SectionSubtermList"])

            if not subterm:
                log_step("EA", index, len(turmas), f"Turma {nome_turma}: sem bimestre ativo, ignorada.")
                continue

            log_step("EA", index, len(turmas), f"Turma {nome_turma}: carregando alunos.")
            alunos = self.api.alunos_da_turma(subterm["Identity"])
            alunos_ativos = [
                [aluno["AcademicId"], aluno["StudentName"]]
                for aluno in alunos
                if aluno["CourseEnrollmentStatus"] == 1
            ]
            dados_json[nome_turma] = {
                "header": ["RA", "Aluno"],
                "rows": alunos_ativos,
            }
            log_progress("EA", f"Turma {nome_turma}: {len(alunos_ativos)} alunos ativos exportados.")

        return dados_json

    def export_to_json(self, output_file: str) -> dict[str, dict[str, list[list[str]]]]:
        log_progress("EA", "Montando carga de alunos.")
        dados_json = self.build_student_payload()
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as arquivo_json:
            json.dump(dados_json, arquivo_json, ensure_ascii=False, indent=2)

        log_progress("EA", f"Arquivo JSON salvo em {output_path}.")
        return dados_json
