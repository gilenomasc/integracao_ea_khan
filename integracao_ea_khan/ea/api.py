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
    
    def get_id_avaliacao_Khan(self, subterm_id):
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

    def grade_save(self, academic_id, course_offering, enrollment_number, identity, natural_person_id, score, student_name, subterm_course_assigned_id, student_id):

        endpoint = "/teacherportal/AssignmentGrades/Save"

        payload = [
            {
                'Notes': None,
                'CourseEnrollmentStatus': 1,
                'ResultOutdated': False,
                'Grade': None,
                'SubtermCourseAssignmentStatus': 0,
                'AcademicId': academic_id,
                'CourseOffering': 'EMERE01MAMATEM',
                'ClassAssignmentId': '4900b461-6092-4d21-9eab-d97ff32dc6ca',
                'EnrollmentNumber': enrollment_number,
                'Identity': identity,
                'NaturalPersonId': natural_person_id,
                'Score': score,
                'StudentName': student_name,
                'SubtermCourseAssignedId': subterm_course_assigned_id,
                'IsInclusionStudent': False,
                'StudentId': student_id,
                'HasOccurrence': False,
                'MeetingDate': None,
                'DeactivateOccurrence': True,
            },
        ]

        r = self.request("POST", endpoint, json=payload)

        return r