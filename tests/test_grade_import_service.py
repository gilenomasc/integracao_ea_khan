import unittest
from unittest.mock import MagicMock

from integracao_ea_khan.ea.grade_import_service import GradeImportError, GradeImportService


class GradeImportServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.api = MagicMock()
        self.service = GradeImportService(self.api)

    def test_import_grades_builds_save_payload_from_grid_and_normalizes_leading_zero_ra(self) -> None:
        self.api.listar_turmas.return_value = [{"CourseOfferingGroup": "EMERE01MA", "SectionSubtermList": [{"Identity": "subterm"}]}]
        self.api.bimestre_atual.return_value = {"Identity": "subterm"}
        self.api.get_class_assignment_id.return_value = "assignment"
        self.api.get_student_grades.return_value = [
            {"AcademicId": "0082954", "StudentName": "Davi", "Score": None, "Identity": "student-1"}
        ]
        response = MagicMock(status_code=200)
        self.api.grade_save.return_value = response
        self.api.session_manager.session = MagicMock()

        result = self.service.import_grades(
            {"Turmas": [{"Nome": "EMERE01MA", "Notas": [{"AcademicId": 82954, "StudentName": "Davi", "Score": 4.5}]}]},
            apply=True,
        )

        self.assertFalse(result["dry_run"])
        self.assertTrue(result["classes"][0]["saved"])
        self.api.grade_save.assert_called_once_with(
            [{"AcademicId": "0082954", "StudentName": "Davi", "Score": 4.5, "Identity": "student-1"}]
        )

    def test_prepare_rejects_grade_for_student_absent_from_grid(self) -> None:
        self.api.listar_turmas.return_value = [{"CourseOfferingGroup": "EMERE01MA", "SectionSubtermList": [{"Identity": "subterm"}]}]
        self.api.bimestre_atual.return_value = {"Identity": "subterm"}
        self.api.get_class_assignment_id.return_value = "assignment"
        self.api.get_student_grades.return_value = []
        self.api.session_manager.session = MagicMock()

        with self.assertRaisesRegex(GradeImportError, "nao encontrado no Grid_Read"):
            self.service.import_grades(
                {"Turmas": [{"Nome": "EMERE01MA", "Notas": [{"AcademicId": 1, "StudentName": "Ausente", "Score": 2.0}]}]}
            )
        self.api.grade_save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
