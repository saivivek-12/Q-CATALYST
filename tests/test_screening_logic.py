"""
Test suite for screening decision rules, boundary thresholds, and evaluation logic.
"""

import unittest
from screening_logic import (
    evaluate,
    evaluate_full,
    get_next_action,
    TARGET_EV,
    SHORTLIST_WINDOW_EV,
    BORDERLINE_WINDOW_EV,
)
from screening_types import (
    ScreeningPolicy,
    CalculatedResult,
    ModelIncompleteResult,
    ValidationFailedResult,
    SingleVqeResult,
)


class TestScreeningLogic(unittest.TestCase):

    def setUp(self):
        self.dummy_vqe = SingleVqeResult(
            vqe_energy_ev=-1.50,
            exact_energy_ev=-1.50,
            absolute_error_ev=1e-15,
            iterations=10,
            evaluations=20,
            converged=True,
        )

    def test_shortlist_decision(self):
        # Proxy within ±0.10 eV -> SHORTLIST
        res = CalculatedResult(
            catalyst_id="Pt",
            formula="Pt",
            name="Platinum",
            category="Noble metal",
            model_type="metal cluster",
            structure="Pt surrogate",
            active_site="under-coordinated site",
            clean=self.dummy_vqe,
            adsorbed=self.dummy_vqe,
            interaction_energy_ev=-0.20,
            thermochemical_correction_ev=0.24,
            her_screening_proxy_ev=0.04,
            distance_from_target_ev=0.04,
            max_vqe_error_ev=1e-15,
            decision="SHORTLIST",
            decision_reason="Proxy is +0.04 eV",
            next_action="High fidelity",
        )
        status, reason = evaluate(res)
        self.assertEqual(status, "SHORTLIST")

    def test_borderline_decision_from_proxy(self):
        # Proxy at 0.15 eV -> BORDERLINE
        res = CalculatedResult(
            catalyst_id="TestCat",
            formula="TC",
            name="Test Candidate",
            category="Transition metal",
            model_type="metal cluster",
            structure="TC surrogate",
            active_site="under-coordinated site",
            clean=self.dummy_vqe,
            adsorbed=self.dummy_vqe,
            interaction_energy_ev=-0.09,
            thermochemical_correction_ev=0.24,
            her_screening_proxy_ev=0.15,
            distance_from_target_ev=0.15,
            max_vqe_error_ev=1e-15,
            decision="BORDERLINE",
            decision_reason="Proxy is +0.15 eV",
            next_action="Refine model",
        )
        status, reason = evaluate(res)
        self.assertEqual(status, "BORDERLINE")

    def test_not_shortlisted_decision(self):
        # Proxy at 0.35 eV -> NOT SHORTLISTED
        res = CalculatedResult(
            catalyst_id="TestCat2",
            formula="TC2",
            name="Test Candidate 2",
            category="Transition metal",
            model_type="metal cluster",
            structure="TC surrogate",
            active_site="under-coordinated site",
            clean=self.dummy_vqe,
            adsorbed=self.dummy_vqe,
            interaction_energy_ev=0.11,
            thermochemical_correction_ev=0.24,
            her_screening_proxy_ev=0.35,
            distance_from_target_ev=0.35,
            max_vqe_error_ev=1e-15,
            decision="NOT SHORTLISTED",
            decision_reason="Proxy is +0.35 eV",
            next_action="Inspect assumptions",
        )
        status, reason = evaluate(res)
        self.assertEqual(status, "NOT SHORTLISTED")

    def test_model_incomplete_decision(self):
        res = ModelIncompleteResult(
            catalyst_id="MoS2",
            formula="MoS₂",
            name="Molybdenum disulfide",
            category="2D dichalcogenide",
            model_type="edge cluster",
            structure="edge surrogate",
            active_site="undefined",
            missing_fields=["phase", "edge termination", "local adsorption geometry"],
            reason="Required definitions missing",
            next_action="Define active site",
        )
        status, reason = evaluate(res)
        self.assertEqual(status, "MODEL INCOMPLETE")

    def test_vqe_validation_failure_decision(self):
        failed_vqe = SingleVqeResult(
            vqe_energy_ev=-1.20,
            exact_energy_ev=-1.50,
            absolute_error_ev=0.30,
            iterations=1,
            evaluations=5,
            converged=False,
        )
        res = ValidationFailedResult(
            catalyst_id="Pt",
            formula="Pt",
            name="Platinum",
            category="Noble metal",
            model_type="metal cluster",
            structure="Pt surrogate",
            active_site="under-coordinated site",
            clean=failed_vqe,
            adsorbed=failed_vqe,
            max_vqe_error_ev=0.30,
            tolerance_ev=1e-5,
            reason="Quantum validation did not pass: error 3.0e-01 eV > 1e-05 eV",
            next_action="Refine quantum ansatz",
        )
        status, reason = evaluate(res)
        self.assertEqual(status, "BORDERLINE")

    def test_next_action_messages(self):
        self.assertIn("higher-fidelity", get_next_action("SHORTLIST"))
        self.assertIn("Refine", get_next_action("BORDERLINE"))
        self.assertIn("Do not discard", get_next_action("NOT SHORTLISTED"))
        self.assertIn("Complete the missing", get_next_action("MODEL INCOMPLETE"))


if __name__ == "__main__":
    unittest.main()
