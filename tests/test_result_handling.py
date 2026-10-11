"""
Test suite ensuring complete robustness against KeyError: 'clean' and UI export crashes.
Tests are designed to be robust against the real-world state of the saved JSON — which
can contain either incomplete OR previously-calculated results for MoS2/WS2/NiMo,
depending on whether the researcher has defined and run those models interactively.
"""

import unittest
import json
import csv
import io
from pathlib import Path
from catalyst_database import get_all_catalysts
from catalyst_models import get_all_models, get_model, configure_active_site_model
from quantum_catalyst_engine import load_results, save_results, calculate
from screening_types import (
    ModelIncompleteResult,
    CalculatedResult,
    ValidationFailedResult,
    result_from_dict,
)
from screening_logic import evaluate


class TestResultHandlingAndExport(unittest.TestCase):

    def test_no_keyerror_on_any_result_type(self):
        """All results in the JSON must be parseable into typed objects without crash."""
        res_file = Path("quantum_screening_results.json")
        self.assertTrue(res_file.exists(), "quantum_screening_results.json must exist")

        results = load_results(res_file)
        self.assertEqual(len(results), 12, f"Expected 12 results, got {len(results)}")

        for cid, r in results.items():
            # Must be a recognised typed object
            self.assertIsInstance(
                r, (CalculatedResult, ModelIncompleteResult, ValidationFailedResult),
                f"{cid}: unexpected result type {type(r)}"
            )
            # Must NEVER crash on .get() for any key
            r.get("clean")
            r.get("adsorbed")
            r.get("max_vqe_error_ev")
            r.get("her_screening_proxy_ev")
            r.get("missing_fields")

    def test_incomplete_models_never_have_vqe_attributes(self):
        """ModelIncompleteResult objects must never expose VQE energy attributes."""
        # Create a fresh incomplete result directly from the engine
        for cid in ["MoS2", "WS2", "NiMo"]:
            m = get_model(cid)
            res = calculate(cid, m)
            if isinstance(res, ModelIncompleteResult):
                self.assertIsNone(res.get("clean"))
                self.assertIsNone(res.get("adsorbed"))
                self.assertIsNone(res.get("max_vqe_error_ev"))
                self.assertEqual(res.decision, "MODEL INCOMPLETE")
                self.assertGreater(len(res.missing_fields), 0)

    def test_export_table_assembly_never_crashes(self):
        """Export logic must generate exactly 12 rows regardless of result state."""
        results = load_results(Path("quantum_screening_results.json"))
        catalysts = get_all_catalysts()
        models = get_all_models()

        export_rows = []
        for cat in catalysts:
            cid = cat["id"]
            r = results.get(cid)
            m = models[cid]

            # This mirrors the exact export logic in app.py
            if r is None or r.is_incomplete:
                missing_str = ", ".join(m.get("missing", [])) if m.get("missing") else "structural definition"
                export_rows.append({
                    "Catalyst": cat["name"],
                    "Formula": cat["formula"],
                    "Category": cat["category"],
                    "Model Completeness": "Incomplete",
                    "Missing Fields": missing_str,
                    "Clean VQE (eV)": "N/A",
                    "Clean Exact (eV)": "N/A",
                    "VQE Error (eV)": "N/A",
                    "Adsorbed VQE (eV)": "N/A",
                    "H* Interaction (eV)": "N/A",
                    "HER Proxy (eV)": "N/A",
                    "Decision": "MODEL INCOMPLETE",
                })
            elif r.is_validation_failed:
                export_rows.append({
                    "Catalyst": cat["name"],
                    "Formula": cat["formula"],
                    "Category": cat["category"],
                    "Model Completeness": "Complete",
                    "Missing Fields": "None",
                    "Clean VQE (eV)": f"{r.clean.vqe_energy_ev:.6f}",
                    "Clean Exact (eV)": f"{r.clean.exact_energy_ev:.6f}",
                    "VQE Error (eV)": f"{r.max_vqe_error_ev:.2e}",
                    "Adsorbed VQE (eV)": f"{r.adsorbed.vqe_energy_ev:.6f}",
                    "H* Interaction (eV)": "N/A",
                    "HER Proxy (eV)": "N/A",
                    "Decision": "BORDERLINE",
                })
            elif r.is_calculated:
                export_rows.append({
                    "Catalyst": cat["name"],
                    "Formula": cat["formula"],
                    "Category": cat["category"],
                    "Model Completeness": "Complete",
                    "Missing Fields": "None",
                    "Clean VQE (eV)": f"{r.clean.vqe_energy_ev:.6f}",
                    "Clean Exact (eV)": f"{r.clean.exact_energy_ev:.6f}",
                    "VQE Error (eV)": f"{r.max_vqe_error_ev:.2e}",
                    "Adsorbed VQE (eV)": f"{r.adsorbed.vqe_energy_ev:.6f}",
                    "H* Interaction (eV)": f"{r.interaction_energy_ev:+.6f}",
                    "HER Proxy (eV)": f"{r.her_screening_proxy_ev:+.6f}",
                    "Decision": r.decision,
                })

        self.assertEqual(len(export_rows), 12, f"Expected 12 rows, got {len(export_rows)}")

        # Write CSV — must not crash
        csv_buf = io.StringIO()
        writer = csv.DictWriter(csv_buf, fieldnames=list(export_rows[0].keys()))
        writer.writeheader()
        writer.writerows(export_rows)
        csv_output = csv_buf.getvalue()

        self.assertIn("Platinum", csv_output)
        self.assertIn("Molybdenum disulfide", csv_output)
        self.assertIn("Nickel–molybdenum", csv_output)

    def test_polymorphic_dict_deserializer(self):
        """result_from_dict must correctly classify raw dict payloads."""
        # Incomplete dict
        raw_incomplete = {
            "catalyst_id": "MoS2",
            "status": "model_incomplete",
            "missing": ["phase", "edge termination"],
        }
        res_inc = result_from_dict(raw_incomplete)
        self.assertIsInstance(res_inc, ModelIncompleteResult)
        self.assertEqual(res_inc.decision, "MODEL INCOMPLETE")

        # Calculated dict
        raw_calc = {
            "catalyst_id": "Pt",
            "status": "calculated",
            "clean": {
                "vqe_energy_ev": -1.51,
                "exact_energy_ev": -1.51,
                "absolute_error_ev": 1e-15,
                "iterations": 10,
                "evaluations": 20,
                "converged": True,
            },
            "adsorbed": {
                "vqe_energy_ev": -1.69,
                "exact_energy_ev": -1.69,
                "absolute_error_ev": 1e-15,
                "iterations": 10,
                "evaluations": 20,
                "converged": True,
            },
            "interaction_energy_ev": -0.18,
            "thermochemical_correction_ev": 0.24,
            "her_screening_proxy_ev": 0.06,
            "decision": "SHORTLIST",
        }
        res_calc = result_from_dict(raw_calc)
        self.assertIsInstance(res_calc, CalculatedResult)
        self.assertEqual(res_calc.decision, "SHORTLIST")

    def test_json_round_trip_integrity(self):
        """All 12 results must survive JSON serialisation and deserialisation without data loss."""
        results_before = load_results(Path("quantum_screening_results.json"))

        # Write to a temp buffer
        tmp = Path("quantum_screening_results_test_tmp.json")
        save_results(tmp, results_before)
        results_after = load_results(tmp)
        tmp.unlink()  # clean up

        self.assertEqual(set(results_before.keys()), set(results_after.keys()))
        for cid in results_before:
            before = results_before[cid]
            after = results_after[cid]
            self.assertEqual(before.status, after.status)
            self.assertEqual(before.decision, after.decision)
            if before.is_calculated:
                self.assertAlmostEqual(
                    before.her_screening_proxy_ev,
                    after.her_screening_proxy_ev,
                    places=10,
                )


if __name__ == "__main__":
    unittest.main()
