import unittest
from unittest.mock import patch

from integracao_ea_khan.ea.occurrence_import_service import OccurrenceImportService


class Response:
    def __init__(self, data=None, text=""):
        self._data = data or {}
        self.text = text

    def json(self):
        return self._data


class FakeOccurrenceAPI:
    session_manager = type("SessionManager", (), {"session": object()})()

    def test_endpoint(self, *_args):
        return True

    def listar_turmas(self, *_args):
        return [{"CourseOfferingGroup": "TURMA 1", "Identity": "section-1", "TermCourseOfferingGroupId": "group-1"}]

    def load_occurrence_type_list(self):
        return {"Items": [{"Code": "42", "Name": "Tipo"}]}

    def class_occurrence_create(self, _section_id):
        return Response(text='var entity = eval({"Occurrence": {"VisualizationDate": null}})')

    def load_students_by_section(self, _section_id):
        return Response({"Data": [{"AcademicId": "0077350", "Identity": "student-1"}]})

    def class_occurrence_save(self, payload):
        self.saved_payload = payload
        return Response()


class OccurrenceImportServiceTestCase(unittest.TestCase):
    @patch("integracao_ea_khan.ea.occurrence_import_service.get_context_ids_cached", return_value=("employee", "term"))
    def test_import_normalizes_leading_zero_ra_and_only_saves_with_apply(self, _context):
        api = FakeOccurrenceAPI()
        payload = {"InfoTurmas": [{"CourseOfferingGroup": "TURMA 1", "StudentList": [77350]}], "Occurrence": {"Type": "42", "Description": "Descricao"}}

        result = OccurrenceImportService(api).import_occurrences(payload, apply=True)

        self.assertFalse(result["dry_run"])
        self.assertTrue(result["classes"][0]["saved"])
        occurrence = api.saved_payload["occurrenceForTeacherPortal"]["Occurrence"]
        self.assertEqual(occurrence["CourseOfferingSection"], {"Identity": "section-1"})
        self.assertEqual(len(api.saved_payload["occurrenceForTeacherPortal"]["StudentList"]), 1)


if __name__ == "__main__":
    unittest.main()
