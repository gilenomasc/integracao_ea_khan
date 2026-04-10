import unittest
from unittest.mock import MagicMock, patch

from integracao_ea_khan.khan.api import KhanTeacherPortalAPI, load_query


class KhanTeacherPortalAPITestCase(unittest.TestCase):
    @patch("integracao_ea_khan.khan.base_client.requests.Session")
    def test_get_progress_by_student_builds_expected_request_and_returns_json(self, session_cls) -> None:
        session_manager = MagicMock()
        session = MagicMock()
        session_cls.return_value = session

        expected_json = {
            "data": {
                "classroom": {
                    "descriptor": "abc123",
                    "assignmentsPage": {
                        "assignments": [{"id": "assignment-1", "title": "Lista 1"}],
                        "pageInfo": {"nextCursor": None},
                    },
                }
            }
        }

        response = MagicMock()
        response.json.return_value = expected_json
        response.raise_for_status.return_value = None
        session.request.return_value = response

        api = KhanTeacherPortalAPI(
            base_url="https://khanacademy.org",
            session_manager=session_manager,
        )

        result = api.get_progress_by_student(
            class_descriptor="abc123",
            page_size=10,
            after="cursor-1",
        )

        self.assertEqual(result, expected_json)
        session_manager.load_cookies.assert_called_once()
        session.request.assert_called_once_with(
            "POST",
            "https://khanacademy.org/api/internal/graphql/ProgressByStudent",
            params={
                "lang": "pt",
                "app": "khanacademy",
            },
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/json",
                "Referer": "https://www.khanacademy.org/teacher/class/abc123/assignment-scores",
                "Origin": "https://www.khanacademy.org",
                "x-ka-fkey": "1",
            },
            json={
                "operationName": "ProgressByStudent",
                "variables": {
                    "classDescriptor": "abc123",
                    "assignmentFilters": {
                        "dueAfter": None,
                        "dueBefore": None,
                        "contentKinds": None,
                        "courseIDs": None,
                    },
                    "after": "cursor-1",
                    "pageSize": 10,
                },
                "query": load_query("get_progress_by_student.graphql"),
            },
        )
        response.raise_for_status.assert_called_once()
        response.json.assert_called_once()


if __name__ == "__main__":
    unittest.main()
