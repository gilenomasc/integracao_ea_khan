from __future__ import annotations
from pathlib import Path

from integracao_ea_khan.progress import log_progress

from .base_client import BaseClient

QUERIES_DIR = Path(__file__).resolve().parents[2] / "queries"


def load_query(filename: str) -> str:
    return (QUERIES_DIR / filename).read_text(encoding="utf-8").strip()


class KhanTeacherPortalAPI(BaseClient):
    def __init__(self, base_url, session_manager, language="pt"):
        super().__init__(
            base_url=base_url,
            session_manager=session_manager,
            auth_expiry_checker=self._is_khan_auth_expired,
        )
        self.language = language

    @staticmethod
    def _is_khan_auth_expired(response) -> bool:
        if response.status_code in {401, 302}:
            return True

        content_type = response.headers.get("Content-Type", "")
        response_url = response.url.lower()

        if "text/html" in content_type and "/login" in response_url:
            return True

        return False

    def get_class_list_raw(self):
        response = self.request(
            "POST",
            "/api/internal/graphql/getClassList",
            params={
                "lang": self.language,
                "app": "khanacademy",
            },
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/json",
                "Referer": "https://www.khanacademy.org/teacher/dashboard",
                "Origin": "https://www.khanacademy.org",
                "x-ka-fkey": "1",
            },
            json={
                "operationName": "getClassList",
                "variables": {},
                "query": load_query("get_class_list.graphql"),
            },
        )
        return self._get_json(response)

    def get_classroom_roster_page(self, class_descriptor, teacher_kaid, signupCode, after=0, page_size=40):
        response = self.request(
            "POST",
            "/api/internal/graphql/getClassroomRoster",
            params={
                "lang": self.language,
                "app": "khanacademy",
            },
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/json",
                "Referer": f"https://www.khanacademy.org/teacher/class/{signupCode}/students",
                "Origin": "https://www.khanacademy.org",
                "x-ka-fkey": "1",
            },
            json={
                "operationName": "getClassroomRoster",
                "variables": {
                    "classDescriptor": class_descriptor,
                    "teacherKaid": teacher_kaid,
                    "after": after,
                    "pageSize": page_size,
                },
                "query": load_query("get_classroom_roster.graphql"),
            },
        )
        return self._get_json(response)
    
    def get_progress_by_student(self, class_descriptor, page_size=40, after=None):
        response = self.request(
            "POST",
            "/api/internal/graphql/ProgressByStudent",
            params={
                "lang": self.language,
                "app": "khanacademy",
            },
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/json",
                "Referer": f"https://www.khanacademy.org/teacher/class/{class_descriptor}/assignment-scores",
                "Origin": "https://www.khanacademy.org",
                "x-ka-fkey": "1",
            },
            json={
                "operationName": "ProgressByStudent",
                "variables": {
                    "classDescriptor": class_descriptor,
                    "assignmentFilters": {
                        'dueAfter': None,
                        'dueBefore': None,
                        'contentKinds': None,
                        'courseIDs': None,
                    },
                    "after": after,
                    "pageSize": page_size,
                },
                "query": load_query("get_progress_by_student.graphql"),
            },
        )
        return self._get_json(response)

    def get_progress_by_student_all_pages(self, class_descriptor, class_name, page_size=40):
        log_progress("KHAN", f"Baixando progresso da turma {class_name}.")
        response_data = self.get_progress_by_student(
            class_descriptor=class_descriptor,
            page_size=page_size,
            after=None,
        )

        classroom = response_data["data"]["classroom"]
        assignments_page = classroom["assignmentsPage"]
        all_assignments = list(assignments_page.get("assignments", []))
        page_info = assignments_page.get("pageInfo", {})
        next_cursor = page_info.get("nextCursor")
        seen_cursors = {next_cursor} if next_cursor is not None else set()
        page_number = 1
        log_progress(
            "KHAN",
            f"Turma {class_name}: pagina {page_number} de progresso carregada, {len(all_assignments)} atividades acumuladas.",
        )

        while next_cursor is not None:
            page_number += 1
            current_cursor = next_cursor
            page_data = self.get_progress_by_student(
                class_descriptor=class_descriptor,
                page_size=page_size,
                after=current_cursor,
            )
            page_assignments = page_data["data"]["classroom"]["assignmentsPage"]
            page_assignments_list = page_assignments.get("assignments", [])
            all_assignments.extend(page_assignments_list)
            next_cursor = page_assignments.get("pageInfo", {}).get("nextCursor")
            log_progress(
                "KHAN",
                f"Turma {class_name}: pagina {page_number} de progresso carregada, {len(all_assignments)} atividades acumuladas.",
            )
            if next_cursor == current_cursor:
                log_progress(
                    "KHAN",
                    f"Turma {class_name}: cursor de progresso repetido ({current_cursor}); interrompendo paginacao para evitar loop.",
                )
                next_cursor = None
                break
            if next_cursor in seen_cursors:
                log_progress(
                    "KHAN",
                    f"Turma {class_name}: cursor de progresso ja visto ({next_cursor}); interrompendo paginacao para evitar loop.",
                )
                next_cursor = None
                break
            if next_cursor is not None:
                seen_cursors.add(next_cursor)
            if not page_assignments_list and next_cursor is not None:
                log_progress(
                    "KHAN",
                    f"Turma {class_name}: pagina sem atividades e com proximo cursor ({next_cursor}); interrompendo paginacao defensivamente.",
                )
                next_cursor = None
                break

        classroom["assignmentsPage"]["assignments"] = all_assignments
        classroom["assignmentsPage"]["pageInfo"]["nextCursor"] = None
        log_progress("KHAN", f"Progresso da turma {class_name} concluido com {len(all_assignments)} atividades.")
        return response_data

    def get_classroom_roster(self, class_descriptor, teacher_kaid, signupCode, page_size=40):
        log_progress("KHAN", f"Baixando roster da turma {signupCode}.")
        response_data = self.get_classroom_roster_page(
            class_descriptor=class_descriptor,
            teacher_kaid=teacher_kaid,
            signupCode=signupCode,
            after=0,
            page_size=page_size,
        )

        classroom = response_data["data"]["classroom"]
        students_page = classroom["studentsPage"]
        all_students = list(students_page.get("students", []))
        next_cursor = students_page.get("nextCursor")
        page_number = 1
        log_progress("KHAN", f"Turma {signupCode}: pagina {page_number} carregada, {len(all_students)} alunos acumulados.")

        while next_cursor is not None:
            page_number += 1
            page_data = self.get_classroom_roster_page(
                class_descriptor=class_descriptor,
                teacher_kaid=teacher_kaid,
                signupCode=signupCode,
                after=next_cursor,
                page_size=page_size,
            )
            page_students = page_data["data"]["classroom"]["studentsPage"]
            all_students.extend(page_students.get("students", []))
            next_cursor = page_students.get("nextCursor")
            log_progress("KHAN", f"Turma {signupCode}: pagina {page_number} carregada, {len(all_students)} alunos acumulados.")

        classroom["studentsPage"]["students"] = all_students
        classroom["studentsPage"]["nextCursor"] = None
        log_progress("KHAN", f"Roster da turma {signupCode} concluido com {len(all_students)} alunos.")
        return response_data
    
    # def get_classrooms(self):
    #     response_data = self.get_class_list_raw()
    #     return response_data["data"]["coach"]["studentLists"]

    def get_class_list_simplified(self):
        log_progress("KHAN", "Buscando lista de turmas.")
        response_data = self.get_class_list_raw()
        coach = response_data["data"]["coach"]
        classrooms = coach["studentLists"]
        teacher_kaid = coach["id"]
        log_progress("KHAN", f"{len(classrooms)} turmas encontradas.")
        return [
            {
                "name": classroom["name"],
                "signupCode": classroom["signupCode"],
                "countStudents": classroom["countStudents"],
                "descriptor": classroom["descriptor"],
                "teacherKaid": teacher_kaid,
                "topics": [topic["title"] for topic in classroom.get("topics", [])],
            }
            for classroom in classrooms
        ]

    @staticmethod
    def build_classroom_roster_from_class_info(classroom, roster_data):
        roster_classroom = roster_data["data"]["classroom"]
        students = roster_classroom.get("studentsPage", {}).get("students", [])

        return {
            "name": classroom["name"],
            "signupCode": classroom["signupCode"],
            "countStudents": classroom["countStudents"],
            "descriptor": classroom["descriptor"],
            "teacherKaid": classroom["teacherKaid"],
            "topics": classroom.get("topics", []),
            "students": students,
        }
