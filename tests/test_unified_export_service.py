import unittest
from pathlib import Path

from integracao_ea_khan.integration.unified_export_service import build_unified_payload, load_json_file

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class UnifiedExportServiceTestCase(unittest.TestCase):
    def test_build_unified_payload_with_real_sample(self) -> None:
        etapa_ea = load_json_file(FIXTURES_DIR / "alunos.json")
        match_result = load_json_file(FIXTURES_DIR / "emere01mc_matches_fast.json")

        payload = build_unified_payload(
            etapa_ea_payload=etapa_ea,
            match_results=[match_result],
            engine="fast",
            etapa_ea_file=FIXTURES_DIR / "alunos.json",
            rosters_dir="tests/classroom_rosters",
            matches_dir=FIXTURES_DIR,
        )

        self.assertEqual(payload["engine"], "fast")
        self.assertEqual(payload["summary"]["classCountMatched"], 1)
        self.assertEqual(payload["summary"]["matchedCount"], 28)
        self.assertIn("EMERE01MC", payload["classes"])


if __name__ == "__main__":
    unittest.main()
