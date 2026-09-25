import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.simulation_engine import generate_projections, STRATEGIES_METADATA
from dashboard.withdrawal_advisor import calculate_withdrawal_advice
from fastapi.testclient import TestClient
from dashboard.app import app

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_simulation_engine_horizons(self):
        for strat_id in ["london_only", "all_sessions", "apex_compliant"]:
            for h in [1, 5, 10]:
                res = generate_projections(strategy_id=strat_id, horizon_years=h, initial_balance=1000.0)
                self.assertIn("scenarios", res)
                self.assertIn("income", res["scenarios"])
                self.assertIn("compounded", res["scenarios"])
                
                # Comprovar longitud de mesos
                expected_len = (h * 12) + 1
                self.assertEqual(len(res["scenarios"]["income"]["balance"]), expected_len)
                self.assertEqual(len(res["labels"]), expected_len)

    def test_withdrawal_advisor_phases(self):
        # 1. Saldo 1.000$ -> Fase 1 (0$ retirada)
        adv1 = calculate_withdrawal_advice(1000.0)
        self.assertEqual(adv1["recommended_monthly_withdrawal"], 0.0)
        self.assertIn("Fase 1", adv1["phase"])

        # 2. Saldo 3.000$ -> Fase 2 (Retirada moderada)
        adv2 = calculate_withdrawal_advice(3000.0)
        self.assertGreater(adv2["recommended_monthly_withdrawal"], 0.0)
        self.assertIn("Fase 2", adv2["phase"])

        # 3. Saldo 10.000$ -> Fase 3 (Renda plena)
        adv3 = calculate_withdrawal_advice(10000.0)
        self.assertEqual(adv3["recommended_monthly_withdrawal"], 1500.0)
        self.assertIn("Fase 3", adv3["phase"])

        # 4. Saldo 25.000$ -> Fase 4 (Búnquer)
        adv4 = calculate_withdrawal_advice(25000.0)
        self.assertEqual(adv4["recommended_monthly_withdrawal"], 2200.0)
        self.assertIn("Fase 4", adv4["phase"])

    def test_api_endpoints(self):
        # GET /api/status
        r_status = self.client.get("/api/status")
        self.assertEqual(r_status.status_code, 200)
        data = r_status.json()
        self.assertIn("cash_balance", data)
        self.assertIn("active_contract", data)

        # GET /api/strategies
        r_strat = self.client.get("/api/strategies")
        self.assertEqual(r_strat.status_code, 200)
        self.assertIn("london_only", r_strat.json())

        # GET /api/projections
        r_proj = self.client.get("/api/projections?strategy=london_only&horizon=5")
        self.assertEqual(r_proj.status_code, 200)
        self.assertIn("scenarios", r_proj.json())

        # GET /api/withdrawal-advice
        r_adv = self.client.get("/api/withdrawal-advice?balance=3500")
        self.assertEqual(r_adv.status_code, 200)
        self.assertGreater(r_adv.json()["recommended_monthly_withdrawal"], 0)

        # GET /api/london-zones
        r_zones = self.client.get("/api/london-zones")
        self.assertEqual(r_zones.status_code, 200)
        self.assertIn("both", r_zones.json())
        self.assertIn("high", r_zones.json())
        self.assertIn("low", r_zones.json())

        # GET / (Index HTML)
        r_index = self.client.get("/")
        self.assertEqual(r_index.status_code, 200)
        self.assertIn("MNQ LONDON ZONES PRO", r_index.text)

if __name__ == "__main__":
    unittest.main()
