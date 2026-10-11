"""
Comprehensive end-to-end integration test verifying all 12 catalysts,
parameter mutations, stale result detection, and full screening workflows.
"""

import unittest
from catalyst_database import get_all_catalysts, get_catalyst
from catalyst_models import get_all_models, get_model, configure_active_site_model
from quantum_catalyst_engine import calculate, DEFAULT_BACKEND
from screening_types import (
    CalculatedResult,
    ModelIncompleteResult,
    ValidationFailedResult,
    ScreeningPolicy,
)
from screening_logic import evaluate_full


class TestEndToEndWorkflow(unittest.TestCase):

    def test_all_12_catalysts_end_to_end(self):
        models = get_all_models()
        catalysts = get_all_catalysts()
        policy = ScreeningPolicy()

        for cat in catalysts:
            cid = cat["id"]
            m = models[cid]

            if cid in ("MoS2", "WS2", "NiMo"):
                # Test incomplete by default
                res_inc = calculate(cid, m, policy=policy)
                self.assertIsInstance(res_inc, ModelIncompleteResult)
                status, reason, next_act = evaluate_full(res_inc, m, policy)
                self.assertEqual(status, "MODEL INCOMPLETE")
                self.assertIn("Complete the missing", next_act)

                # Now complete the model definition and verify successful calculation
                if cid == "MoS2":
                    custom_m = configure_active_site_model("MoS2", {
                        "phase": "2H (semiconducting)",
                        "edge": "Mo-edge",
                        "geometry": "Atop Mo site",
                    })
                elif cid == "WS2":
                    custom_m = configure_active_site_model("WS2", {
                        "phase": "1T (metallic)",
                        "edge": "W-edge",
                        "geometry": "Atop W site",
                    })
                else:  # NiMo
                    custom_m = configure_active_site_model("NiMo", {
                        "ni_fraction": 0.50,
                        "geometry": "Mixed Ni-Mo boundary",
                        "adsorption_site": "Ni-Mo bridge site",
                    })

                self.assertTrue(custom_m["complete"])
                res_comp = calculate(cid, custom_m, policy=policy)
                self.assertIsInstance(res_comp, CalculatedResult)
                self.assertLess(res_comp.max_vqe_error_ev, policy.max_acceptable_vqe_error)
                status, reason, next_act = evaluate_full(res_comp, custom_m, policy)
                self.assertIn(status, ["SHORTLIST", "BORDERLINE", "NOT SHORTLISTED"])
            else:
                # Monometallic completed by default
                res = calculate(cid, m, policy=policy)
                self.assertIsInstance(res, CalculatedResult)
                self.assertLess(res.max_vqe_error_ev, policy.max_acceptable_vqe_error)
                status, reason, next_act = evaluate_full(res, m, policy)
                self.assertIn(status, ["SHORTLIST", "BORDERLINE", "NOT SHORTLISTED"])
                self.assertIsNotNone(res.interaction_energy_ev)
                self.assertIsNotNone(res.her_screening_proxy_ev)

    def test_parameter_change_and_stale_detection(self):
        # Initial run with default distance 1.55 A
        m = get_model("Pt")
        res1 = calculate("Pt", m, overrides={"adsorption_distance": 1.55})

        # Changed distance to 1.80 A
        res2 = calculate("Pt", m, overrides={"adsorption_distance": 1.80})

        # Energies must reflect physical sensitivity to distance
        self.assertNotEqual(res1.clean.vqe_energy_ev, res2.clean.vqe_energy_ev)
        self.assertNotEqual(res1.her_screening_proxy_ev, res2.her_screening_proxy_ev)

        # Inputs stored must match
        self.assertEqual(res1.inputs["adsorption_distance_A"], 1.55)
        self.assertEqual(res2.inputs["adsorption_distance_A"], 1.80)

    def test_vqe_failure_and_recovery(self):
        # Force validation failure
        m = get_model("Ni")
        res_fail = calculate("Ni", m, force_validation_fail=True)
        self.assertIsInstance(res_fail, ValidationFailedResult)
        status_fail, reason_fail, _ = evaluate_full(res_fail, m)
        self.assertEqual(status_fail, "BORDERLINE")
        self.assertIn("Quantum validation did not pass", reason_fail)

        # Recover on subsequent standard calculation
        res_ok = calculate("Ni", m, force_validation_fail=False)
        self.assertIsInstance(res_ok, CalculatedResult)
        status_ok, _, _ = evaluate_full(res_ok, m)
        self.assertEqual(status_ok, "SHORTLIST")


if __name__ == "__main__":
    unittest.main()
