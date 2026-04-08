from datetime import datetime

from .base_client import BaseClient

class TeacherPortalAPI(BaseClient):

    def listar_turmas(self, employee_id, academic_term_id):

        endpoint = "/teacherportal/Home/GetListOpenedSectionByEmployee"

        payload = {
            "sort": "",
            "group": "",
            "filter": "",
            "employeeId": employee_id,
            "academicTermId": academic_term_id,
            "programOfferedId": "",
            "courseId": ""
        }

        r = self.request("POST", endpoint, data=payload)

        return self._get_data(r)

    def alunos_da_turma(self, subterm_id):

        endpoint = "/teacherportal/ClassAttendanceDaily/Grid_Read"

        payload = {
            "sort": "",
            "group": "",
            "filter": "",
            "courseOfferingSectionSubtermId": subterm_id
        }

        r = self.request("POST", endpoint, data=payload)

        return self._get_data(r)
    
    def test_endpoint(self, employee_id, academic_term_id):

        endpoint = "/teacherportal/Home/GetListOpenedSectionJoinByEmployee"

        payload = {
            "sort": "",
            "group": "",
            "filter": "",
            "employeeId": employee_id,
            "academicTermId": academic_term_id,
            "programOfferedId": "",
            "courseId": ""
        } 

        r = self.request("POST", endpoint, data=payload)

        return r.status_code == 200
    
    def bimestre_atual(self, section_subterms):

        agora = datetime.now()

        for subterm in section_subterms:

            inicio = datetime.strptime(
                subterm["AcademicSubterm"]["StartDate"],
                "%Y/%m/%d %H:%M:%S"
            )

            fim = datetime.strptime(
                subterm["AcademicSubterm"]["EndDate"],
                "%Y/%m/%d %H:%M:%S"
            )

            if inicio <= agora <= fim:
                return subterm
