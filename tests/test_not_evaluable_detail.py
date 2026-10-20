# ============================================================
# ROMANTIK AI API
# TESTS — NOT EVALUABLE DETAIL IN REVIEW RESPONSE
# ============================================================

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from app.api.routes import review_form
from app.schemas.review import (
    ReviewRequest,
    ReviewResponse,
    RBSSummary,
    RBSFinding,
    RBSNotEvaluable,
)


class TestNotEvaluableDetailResponse(unittest.TestCase):
    """
    Pengujian detail aturan berstatus not_evaluable
    pada response endpoint review.
    """

    @classmethod
    def setUpClass(cls):
        project_root = Path(__file__).resolve().parents[1]
        cls.sample_path = (
            project_root
            / "data"
            / "sample_input"
            / "sample_58594.json"
        )
        with cls.sample_path.open("r", encoding="utf-8") as f:
            cls.sample_data = json.load(f)

    @patch("app.services.review_service.generate_review")
    def test_response_with_3_not_evaluable_counts_and_len(
        self,
        mock_gen,
    ):
        """
        1. response dengan 3 not_evaluable:
           - n_not_evaluable == 3
           - len(not_evaluable) == 3
        """
        mock_gen.return_value = {
            "status": "generated",
            "review_html": "<p>Catatan evaluasi Hybrid AI.</p>",
        }

        req = ReviewRequest(form=self.sample_data)
        response = review_form(req)

        self.assertEqual(response.status, "success")
        self.assertEqual(response.rbs.n_not_evaluable, 3)
        self.assertEqual(len(response.rbs.not_evaluable), 3)

    @patch("app.services.review_service.generate_review")
    def test_each_not_evaluable_item_has_rule_id(
        self,
        mock_gen,
    ):
        """
        2. setiap item memiliki rule_id yang valid.
        """
        mock_gen.return_value = {
            "status": "generated",
            "review_html": "<p>Catatan evaluasi Hybrid AI.</p>",
        }

        req = ReviewRequest(form=self.sample_data)
        response = review_form(req)

        rule_ids = [
            item.rule_id
            for item in response.rbs.not_evaluable
        ]
        for rule_id in rule_ids:
            self.assertTrue(bool(rule_id))
            self.assertTrue(rule_id.startswith("R-"))

        self.assertEqual(
            rule_ids,
            ["R-V-12", "R-V-11", "R-III-04"],
        )

    @patch("app.services.review_service.generate_review")
    def test_reason_and_evidence_preserved(
        self,
        mock_gen,
    ):
        """
        3. reason dan evidence dipertahankan jika tersedia.
        """
        mock_gen.return_value = {
            "status": "generated",
            "review_html": "<p>Catatan evaluasi Hybrid AI.</p>",
        }

        req = ReviewRequest(form=self.sample_data)
        response = review_form(req)

        items_by_id = {
            item.rule_id: item
            for item in response.rbs.not_evaluable
        }

        # R-V-12
        item_v12 = items_by_id["R-V-12"]
        self.assertEqual(item_v12.status, "not_evaluable")
        self.assertEqual(item_v12.applicability, "applicable")
        self.assertEqual(
            item_v12.reason,
            "sampling_error_unavailable_or_conflicting",
        )
        self.assertIsInstance(item_v12.evidence, dict)
        self.assertIn("sampling_error", item_v12.evidence)

        # R-V-11
        item_v11 = items_by_id["R-V-11"]
        self.assertEqual(item_v11.status, "not_evaluable")
        self.assertEqual(item_v11.applicability, "applicable")
        self.assertEqual(
            item_v11.reason,
            "sampling_error_unavailable_or_conflicting",
        )
        self.assertIsInstance(item_v11.evidence, dict)
        self.assertIn("threshold_percent", item_v11.evidence)

        # R-III-04
        item_iii04 = items_by_id["R-III-04"]
        self.assertEqual(item_iii04.status, "not_evaluable")
        self.assertEqual(item_iii04.applicability, "applicable")
        self.assertEqual(
            item_iii04.reason,
            "historical_submission_date_unreliable",
        )
        self.assertIsInstance(item_iii04.evidence, dict)
        self.assertIn("evaluation_context", item_iii04.evidence)

    @patch("app.services.review_service.generate_review")
    def test_findings_remain_unchanged(
        self,
        mock_gen,
    ):
        """
        4. findings tetap tidak berubah.
        """
        mock_gen.return_value = {
            "status": "generated",
            "review_html": "<p>Catatan evaluasi Hybrid AI.</p>",
        }

        req = ReviewRequest(form=self.sample_data)
        response = review_form(req)

        self.assertEqual(response.rbs.n_findings, 6)
        self.assertEqual(len(response.rbs.findings), 6)

        finding_rule_ids = [
            f.rule_id
            for f in response.rbs.findings
        ]
        expected_ids = [
            "R-VII-03",
            "R-I-02A",
            "R-III-08A",
            "R-III-10",
            "R-V-02",
            "R-VII-04",
        ]
        self.assertEqual(finding_rule_ids, expected_ids)

        # Pastikan severity dan message ada
        for f in response.rbs.findings:
            self.assertIn(f.severity, ["error", "warning", "info"])
            self.assertTrue(bool(f.message))

    @patch("app.services.review_service.generate_review")
    def test_hybrid_review_remains_unchanged(
        self,
        mock_gen,
    ):
        """
        5. hybrid_review tetap tidak berubah.
        """
        expected_html = "<p>Paragraf evaluasi model LLM tanpa perubahan.</p>"
        mock_gen.return_value = {
            "status": "generated",
            "review_html": expected_html,
        }

        req = ReviewRequest(form=self.sample_data)
        response = review_form(req)

        self.assertEqual(
            response.hybrid_review,
            expected_html,
        )

    @patch("app.api.routes.run_review_pipeline")
    def test_response_with_0_not_evaluable(
        self,
        mock_pipeline,
    ):
        """
        6. response dengan 0 not_evaluable menghasilkan:
           n_not_evaluable = 0
           not_evaluable = []
        """
        mock_pipeline.return_value = {
            "canonical_record": {
                "id_trans": "99999",
                "nama_kegiatan": "Kegiatan Uji Tanpa Not Evaluable",
                "tahun_kegiatan": "2026",
                "instansi": "BPS",
            },
            "rbs_results": [
                {
                    "rule_id": "R-I-01",
                    "status": "pass",
                    "violation": False,
                    "applicability": "applicable",
                    "reason": "ok",
                    "evidence": {},
                },
                {
                    "rule_id": "R-VI-05",
                    "status": "violation",
                    "violation": True,
                    "severity": "warning",
                    "message": "Peringatan supervisor",
                    "evidence": {"supervisor": 10},
                },
            ],
            "rbs_findings": [
                {
                    "rule_id": "R-VI-05",
                    "severity": "warning",
                    "message": "Peringatan supervisor",
                    "evidence": {"supervisor": 10},
                },
            ],
            "llm_result": {
                "status": "generated",
                "review_html": "<p>Review AI</p>",
            },
        }

        req = ReviewRequest(form={"dummy": "data"})
        response = review_form(req)

        self.assertEqual(response.rbs.n_not_evaluable, 0)
        self.assertEqual(response.rbs.not_evaluable, [])
        self.assertEqual(response.rbs.n_findings, 1)
        self.assertEqual(len(response.rbs.findings), 1)

    @patch("app.services.review_service.generate_review")
    def test_no_pass_rules_in_response(
        self,
        mock_gen,
    ):
        """
        Memastikan rule berstatus pass tidak pernah dikirimkan
        ke findings maupun not_evaluable.
        """
        mock_gen.return_value = {
            "status": "generated",
            "review_html": "<p>Review</p>",
        }

        req = ReviewRequest(form=self.sample_data)
        response = review_form(req)

        # not_evaluable hanya boleh status not_evaluable
        for item in response.rbs.not_evaluable:
            self.assertEqual(item.status, "not_evaluable")
            self.assertNotEqual(item.status, "pass")

        # findings hanya rule pelanggaran
        for f in response.rbs.findings:
            self.assertNotEqual(f.rule_id, "")

    @patch("app.services.review_service.generate_review")
    def test_count_consistency(
        self,
        mock_gen,
    ):
        """
        Memastikan rbs.n_not_evaluable == len(rbs.not_evaluable).
        """
        mock_gen.return_value = {
            "status": "generated",
            "review_html": "<p>Review</p>",
        }

        req = ReviewRequest(form=self.sample_data)
        response = review_form(req)

        self.assertEqual(
            response.rbs.n_not_evaluable,
            len(response.rbs.not_evaluable),
        )
        self.assertEqual(
            response.rbs.n_findings,
            len(response.rbs.findings),
        )


if __name__ == "__main__":
    unittest.main()
