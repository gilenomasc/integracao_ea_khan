import unittest
import uuid
from pathlib import Path
from unittest.mock import MagicMock
import shutil

from integracao_ea_khan.khan.progress_export_service import KhanProgressExportService
from integracao_ea_khan.integration.unified_export_service import load_json_file, write_json_file


class ProgressExportServiceTestCase(unittest.TestCase):
    def test_export_from_unified_file_writes_raw_progress_files_and_manifest(self) -> None:
        api = MagicMock()
        api.get_progress_by_student_all_pages.return_value = {
            "data": {
                "classroom": {
                    "descriptor": "descriptor-1",
                    "studentKaidsAndNicknames": [
                        {"id": "kaid-1", "coachNickname": "Apelido Khan"},
                    ],
                    "assignmentsPage": {
                        "assignments": [
                            {
                                "id": "assignment-1",
                                "title": "Lista 1",
                                "dueDate": "2026-04-10T03:00:00Z",
                                "contents": [{"translatedTitle": "Soma de números negativos"}],
                                "itemCompletionStates": [
                                    {
                                        "studentKaid": "kaid-1",
                                        "bestScore": {"numCorrect": 8, "numAttempted": 10},
                                        "state": "completed",
                                        "student": {"kaid": "kaid-1"},
                                    }
                                ],
                            },
                            {"id": "assignment-2"},
                        ],
                        "pageInfo": {"nextCursor": None},
                    },
                }
            }
        }
        service = KhanProgressExportService(api)

        temp_path = Path(__file__).resolve().parent / f"_tmp_progress_{uuid.uuid4().hex}"
        temp_path.mkdir(parents=True, exist_ok=True)
        try:
            unified_file = temp_path / "unified_matches.json"
            output_dir = temp_path / "progress_raw"
            index_file = temp_path / "progress_raw_index.json"
            simplified_file = temp_path / "progress_simplified.json"
            roster_file = temp_path / "emere01mc_roster.json"

            write_json_file(
                roster_file,
                {
                    "students": [
                        {
                            "kaid": "kaid-1",
                            "username": "aluno.khan",
                            "coachNickname": "Apelido Khan",
                            "profileRoot": "/profile/aluno.khan/",
                        }
                    ]
                },
            )

            write_json_file(
                unified_file,
                {
                    "generatedAt": "2026-04-11T10:00:00",
                    "classes": {
                        "EMERE01MC": {
                            "className": "EMERE01MC",
                            "descriptor": "descriptor-1",
                            "signupCode": "VCWFE7QM",
                            "teacherKaid": "teacher-1",
                            "rosterFile": str(roster_file),
                        },
                        "SEM_DESCRIPTOR": {
                            "className": "SEM_DESCRIPTOR",
                            "signupCode": "ABC12345",
                        },
                    },
                },
            )

            manifest = service.export_from_unified_file(
                unified_file=unified_file,
                output_dir=output_dir,
                index_output_file=index_file,
                simplified_output_file=simplified_file,
            )

            api.get_progress_by_student_all_pages.assert_called_once_with(
                class_descriptor="descriptor-1",
                class_name="EMERE01MC",
                page_size=40,
            )
            self.assertEqual(manifest["exportedCount"], 1)
            self.assertEqual(manifest["skippedCount"], 1)
            self.assertIn("EMERE01MC", manifest["classes"])

            progress_file = Path(manifest["classes"]["EMERE01MC"]["progressFile"])
            self.assertTrue(progress_file.exists())
            self.assertEqual(load_json_file(progress_file)["data"]["classroom"]["descriptor"], "descriptor-1")

            saved_manifest = load_json_file(index_file)
            self.assertEqual(saved_manifest["exportedCount"], 1)
            self.assertEqual(saved_manifest["skipped"][0]["reason"], "missing_descriptor")

            simplified_payload = load_json_file(simplified_file)
            simplified_class = simplified_payload["classes"]["EMERE01MC"]
            self.assertEqual(simplified_class["activities"][0]["contentTitle"], "Soma de números negativos")
            self.assertEqual(simplified_class["activities"][0]["students"][0]["name"], "Apelido Khan")
            self.assertEqual(simplified_class["activities"][0]["students"][0]["grade"], 80.0)
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
