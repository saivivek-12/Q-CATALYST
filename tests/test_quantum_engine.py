"""
Test suite for quantum catalyst engine, Qiskit Hamiltonian, VQE, and exact validation.
"""

import unittest
import numpy as np
from catalyst_models import get_model, configure_active_site_model
from quantum_catalyst_engine import (
    DEFAULT_BACKEND,
    ReducedModelBackend,
    FuturePsi4Backend,
    calculate,
)
from screening_types import (
    CalculatedResult,
    ValidationFailedResult,
    ModelIncompleteResult,
    ScreeningPolicy,
)


class TestQuantumEngine(unittest.TestCase):

    def test_backend_hamiltonian_building(self):
        backend = ReducedModelBackend()
        model = get_model("Pt")
        h_clean = backend.build_hamiltonian(model, adsorbed=False, inputs={})
        h_ads = backend.build_hamiltonian(model, adsorbed=True, inputs={})

        self.assertEqual(h_clean.num_qubits, 2)
        self.assertEqual(h_ads.num_qubits, 2)

        # Adsorbed energy ground state must be lower than clean ground state due to bonding
        clean_mat = h_clean.to_matrix()
        ads_mat = h_ads.to_matrix()
        e_clean = float(np.linalg.eigvalsh(clean_mat)[0].real)
        e_ads = float(np.linalg.eigvalsh(ads_mat)[0].real)
        self.assertLess(e_ads, e_clean)
        self.assertLess(e_ads - e_clean, 0.0)

    def test_vqe_exact_validation(self):
        backend = ReducedModelBackend()
        model = get_model("Pt")
        hamiltonian = backend.build_hamiltonian(model, adsorbed=False, inputs={})
        res = backend.run_vqe(hamiltonian, max_iter=300, gtol=1e-8)

        # Must solve identical operator
        self.assertLess(res.absolute_error_ev, 1e-5, f"VQE error too high: {res.absolute_error_ev}")
        self.assertAlmostEqual(res.vqe_energy_ev, res.exact_energy_ev, places=5)

    def test_calculate_monometallic(self):
        # Test calculation across multiple metals
        for cid in ["Pt", "Ni", "Ru", "Mo"]:
            m = get_model(cid)
            res = calculate(cid, m)
            self.assertIsInstance(res, CalculatedResult)
            self.assertLess(res.max_vqe_error_ev, 1e-5)
            self.assertIn(res.decision, ["SHORTLIST", "BORDERLINE", "NOT SHORTLISTED"])
            self.assertIsNotNone(res.interaction_energy_ev)
            self.assertIsNotNone(res.her_screening_proxy_ev)

    def test_incomplete_model_handling(self):
        # MoS2 incomplete returns ModelIncompleteResult without running VQE
        m = get_model("MoS2")
        res = calculate("MoS2", m)
        self.assertIsInstance(res, ModelIncompleteResult)
        self.assertEqual(res.decision, "MODEL INCOMPLETE")
        self.assertIn("phase", res.missing_fields)

    def test_vqe_failure_simulation(self):
        # Simulating VQE validation failure produces ValidationFailedResult
        m = get_model("Pt")
        res = calculate("Pt", m, force_validation_fail=True)
        self.assertIsInstance(res, ValidationFailedResult)
        self.assertEqual(res.decision, "BORDERLINE")
        self.assertIn("Quantum validation did not pass", res.reason)

    def test_future_psi4_backend_interface(self):
        backend = FuturePsi4Backend()
        self.assertFalse(backend.available)
        with self.assertRaises(NotImplementedError):
            backend.build_hamiltonian({}, False, {})


if __name__ == "__main__":
    unittest.main()
