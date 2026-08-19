from integracao_ea_khan.ea.api import TeacherPortalAPI
from integracao_ea_khan.ea.session_manager import SessionManager
from integracao_ea_khan.ea.settings import settings

EMAIL = "proffernandaalopes@gmail.com"
SENHA = "UN@XP0909"

session_manager = SessionManager(
    session=None,
    auth_file=str(settings.auth_file),
    email=EMAIL,
    password=SENHA,
)

api = TeacherPortalAPI(
    base_url=settings.base_url,
    session_manager=session_manager,
)

endpoint = "/teacherportal/AssignmentGrades/Grid_Read"
payload = {
    "sort": "",
    "group": "",
    "filter": "",
    "classAssignmentId": "de6a861f-3bb6-4afb-9227-07ea2c770dfd",
}
r = api.request("POST", endpoint, data=payload)
    

json_data = [
    {
      "Notes": None,
      "CourseEnrollmentStatus": 1,
      "ResultOutdated": False,
      "Grade": None,
      "SubtermCourseAssignmentStatus": 0,
      "AcademicId": "62996",
      "CourseOffering": "EMERE01MAMATEM",
      "ClassAssignmentId": "de6a861f-3bb6-4afb-9227-07ea2c770dfd",
      "EnrollmentNumber": 1,
      "Identity": "8702f0d2-a65d-4463-85c2-d4eaf6369796",
      "NaturalPersonId": "21c28df2-a72f-412b-8ebf-1266ba54b25b",
      "Score": 2.0,
      "StudentName": "Catarina Oliveira Nunes",
      "SubtermCourseAssignedId": "df32907e-74f8-472f-bc28-8aac9839db64",
      "IsInclusionStudent": False,
      "StudentId": "a6cfa117-e4f7-487f-89aa-9bde0180a942",
      "HasOccurrence": False
    },
    {
      "Notes": None,
      "CourseEnrollmentStatus": 1,
      "ResultOutdated": False,
      "Grade": None,
      "SubtermCourseAssignmentStatus": 0,
      "AcademicId": "63652",
      "CourseOffering": "EMERE01MAMATEM",
      "ClassAssignmentId": "de6a861f-3bb6-4afb-9227-07ea2c770dfd",
      "EnrollmentNumber": 3,
      "Identity": "0872b8b7-5c29-49dd-ae3d-1c059fd7d59f",
      "NaturalPersonId": "9c69cab2-92f6-4440-b7c7-8f73939fec0f",
      "Score": 1.0,
      "StudentName": "Felipe Caroci Senti da Costa",
      "SubtermCourseAssignedId": "8eeb9d87-3bef-4257-9cb5-e5801e16ee29",
      "IsInclusionStudent": False,
      "StudentId": "2e6c836c-2502-4259-a3c7-e1e49b4ef7f8",
      "HasOccurrence": False
    },
]
r = api.grade_save(json_data)

print("status:", r.status_code)
print("location:", r.headers.get("Location"))
print(r.text[:2000])
