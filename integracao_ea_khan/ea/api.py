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
    
    def get_class_assignment_id(self, subterm_id):
        endpoint = "/teacherportal/EvaluatedAssignment/Grid_Read"
        payload = {
            "sort": "",
            "group": "",
            "filter": "",
            "courseOfferingSectionSubtermId": subterm_id
        }
        r = self.request("POST", endpoint, data=payload)
        ret = self._get_data(r)
        
        if not ret:
            return None
        
        return ret[0].get("Identity")
    
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

    def grade_save(self, json_payload):

        endpoint = "/teacherportal/AssignmentGrades/Save"
        r = self.request("POST", endpoint, json=json_payload)
        return r

    def get_student_grades(self, class_assignment_id):

        endpoint = "/teacherportal/AssignmentGrades/Grid_Read"
        payload = {
            "sort": "",
            "group": "",
            "filter": "",
            "classAssignmentId": class_assignment_id
        }
        r = self.request("POST", endpoint, data=payload)
        return self._get_data(r)

    def load_occurrence_type_list(self):
        endpoint = "/teacherportal/ClassOcurrence/GetListOccurrenceTypeByFilter"
        params = {
            "filter": "",
            "numRows": "100",
            "pageIndex": "0",
            "category": "Todos",
        }
        return self.request("POST", endpoint, params=params).json()

    def load_students_by_section(self, section_id):
        endpoint = "/teacherportal/ClassOcurrence/GetListStudentByCourseOfferingSectionForTeacherPortal"
        params = {
            "sort": "",
            "group": "",
            "filter": "",
            "sectionId": section_id,
        }
        return self.request("POST", endpoint, params=params)

    def class_occurrence_create(self, section_id):
        endpoint = "/teacherportal/ClassOcurrence/Create"
        return self.request("POST", endpoint, json={"courseOfferingSectionId": section_id})

    def class_occurrence_save(self, payload):
        endpoint = "/teacherportal/ClassOcurrence/Save"
        return self.request("POST", endpoint, json=payload)
