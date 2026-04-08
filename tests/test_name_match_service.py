import unittest
from pathlib import Path

from integracao_ea_khan.matching.name_match_service import benchmark_matchers, match_students

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class NameMatchServiceTestCase(unittest.TestCase):
    def test_real_files_baseline_match_expected_count(self) -> None:
        import json

        with (FIXTURES_DIR / "alunos.json").open(encoding="utf-8") as file:
            etapa_ea = json.load(file)
        with (FIXTURES_DIR / "emere01mc_VCWFE7QM.json").open(encoding="utf-8") as file:
            roster = json.load(file)

        result = match_students(etapa_ea, roster, "EMERE01MC", engine="baseline")

        self.assertEqual(result["matchedCount"], 28)
        self.assertEqual(len(result["warnings"]), 0)

        matched = {
            row["school_name"]: row["khan_username"]
            for row in result["results"]
            if row["status"] == "matched"
        }
        self.assertEqual(matched["Ana Beatriz Freitas dos Santos"], "anabeatrizfreitas")
        self.assertEqual(matched["Layla Lopes Lima"], "laylalopeslima1606")
        self.assertEqual(matched["Vitória da França Stenz"], "vitoriaf.stenz")

    def test_real_files_fast_matches_baseline_assignments(self) -> None:
        import json

        with (FIXTURES_DIR / "alunos.json").open(encoding="utf-8") as file:
            etapa_ea = json.load(file)
        with (FIXTURES_DIR / "emere01mc_VCWFE7QM.json").open(encoding="utf-8") as file:
            roster = json.load(file)

        baseline = match_students(etapa_ea, roster, "EMERE01MC", engine="baseline")
        fast = match_students(etapa_ea, roster, "EMERE01MC", engine="fast")

        baseline_pairs = {
            row["school_name"]: row["khan_username"]
            for row in baseline["results"]
            if row["khan_username"]
        }
        fast_pairs = {
            row["school_name"]: row["khan_username"]
            for row in fast["results"]
            if row["khan_username"]
        }

        self.assertEqual(fast["matchedCount"], baseline["matchedCount"])
        self.assertEqual(fast_pairs, baseline_pairs)

    def test_khan_top_tie_stays_blank(self) -> None:
        etapa_ea = {
            "TURMA": {
                "header": ["RA", "Aluno"],
                "rows": [
                    ["1", "Ana Maria"],
                    ["2", "Maria Ana"],
                ],
            }
        }
        roster = {
            "name": "TURMA",
            "students": [
                {
                    "kaid": "kaid_1",
                    "coachNickname": "Ana Maria",
                    "username": "anamaria",
                },
                {
                    "kaid": "kaid_2",
                    "coachNickname": "Maria",
                    "username": "maria",
                },
            ],
        }

        result = match_students(etapa_ea, roster, "TURMA", engine="baseline")

        self.assertTrue(any(warning["kind"] == "khan_top_tie" for warning in result["warnings"]))
        ana_row = next(row for row in result["results"] if row["school_name"] == "Ana Maria")
        maria_ana_row = next(row for row in result["results"] if row["school_name"] == "Maria Ana")
        self.assertEqual(ana_row["khan_username"], "anamaria")
        self.assertIsNone(maria_ana_row["khan_username"])

    def test_min_score_can_reject_weak_match(self) -> None:
        etapa_ea = {
            "TURMA": {
                "header": ["RA", "Aluno"],
                "rows": [["1", "Joao Pedro"]],
            }
        }
        roster = {
            "name": "TURMA",
            "students": [
                {
                    "kaid": "kaid_1",
                    "coachNickname": "Carlos",
                    "username": "carlos",
                }
            ],
        }

        result = match_students(etapa_ea, roster, "TURMA", min_score=1_000, engine="fast")

        self.assertEqual(result["matchedCount"], 0)
        self.assertIsNone(result["results"][0]["khan_username"])

    def test_benchmark_reports_same_assignments(self) -> None:
        import json

        with (FIXTURES_DIR / "alunos.json").open(encoding="utf-8") as file:
            etapa_ea = json.load(file)
        with (FIXTURES_DIR / "emere01mc_VCWFE7QM.json").open(encoding="utf-8") as file:
            roster = json.load(file)

        benchmark = benchmark_matchers(etapa_ea, roster, "EMERE01MC", repetitions=2)

        self.assertTrue(benchmark["sameAssignments"])
        self.assertEqual(benchmark["baseline"]["matchedCount"], 28)
        self.assertEqual(benchmark["fast"]["matchedCount"], 28)


if __name__ == "__main__":
    unittest.main()
