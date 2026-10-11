"""
Test suite for catalyst database and active-site models.
"""

import unittest
from catalyst_database import get_all_catalysts, get_catalyst, get_catalyst_map
from catalyst_models import get_all_models, get_model, configure_active_site_model


class TestCatalystDatabaseAndModels(unittest.TestCase):

    def test_all_12_catalysts_present(self):
        cats = get_all_catalysts()
        self.assertEqual(len(cats), 12)
        expected_ids = {"Pt", "Ru", "Ir", "Pd", "Ni", "Co", "Fe", "Mo", "W", "MoS2", "WS2", "NiMo"}
        actual_ids = {c["id"] for c in cats}
        self.assertEqual(expected_ids, actual_ids)

    def test_catalyst_models_match(self):
        models = get_all_models()
        self.assertEqual(len(models), 12)
        for cid in models:
            cat = get_catalyst(cid)
            self.assertIsNotNone(cat)
            m = models[cid]
            self.assertIn("chi", m)
            self.assertIn("d_level", m)
            self.assertIn("coordination", m)
            self.assertIn("coupling", m)
            self.assertIn("affinity", m)
            self.assertIn("site_factor", m)

    def test_default_completeness(self):
        # The 9 monometallic catalysts are complete by default
        complete_ids = ["Pt", "Ru", "Ir", "Pd", "Ni", "Co", "Fe", "Mo", "W"]
        for cid in complete_ids:
            m = get_model(cid)
            self.assertTrue(m["complete"], f"{cid} should be complete by default")
            self.assertEqual(len(m["missing"]), 0)

        # The 3 complex catalysts are incomplete by default
        incomplete_ids = ["MoS2", "WS2", "NiMo"]
        for cid in incomplete_ids:
            m = get_model(cid)
            self.assertFalse(m["complete"], f"{cid} should be incomplete by default")
            self.assertGreater(len(m["missing"]), 0)

    def test_custom_active_site_configuration(self):
        # MoS2 incomplete when geometry missing
        m_inc = configure_active_site_model("MoS2", {
            "phase": "2H (semiconducting)",
            "edge": "Mo-edge",
            "geometry": "Not defined (Incomplete)",
        })
        self.assertFalse(m_inc["complete"])
        self.assertIn("local adsorption geometry", m_inc["missing"])

        # MoS2 complete when all defined
        m_comp = configure_active_site_model("MoS2", {
            "phase": "2H (semiconducting)",
            "edge": "Mo-edge",
            "geometry": "Atop Mo site",
        })
        self.assertTrue(m_comp["complete"])
        self.assertEqual(len(m_comp["missing"]), 0)

        # NiMo complete when defined
        m_nimo = configure_active_site_model("NiMo", {
            "ni_fraction": 0.60,
            "geometry": "Mixed Ni-Mo boundary",
            "adsorption_site": "Ni-Mo bridge site",
        })
        self.assertTrue(m_nimo["complete"])
        self.assertEqual(len(m_nimo["missing"]), 0)


if __name__ == "__main__":
    unittest.main()
