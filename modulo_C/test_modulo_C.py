import unittest
import os
from modulo_B.graph.graph import Graph
from modulo_C.analysis.impact import SETImpactAnalyzer
from modulo_C.analysis.pert import Task, get_setp_phase2_planning
from modulo_C.analysis.nash import NashSolver, GameSolver

class TestModuloC(unittest.TestCase):
    def setUp(self):
        self.g = Graph()
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sincelejo_v2.csv")
        self.g.load_from_csv(csv_path)

    def test_impact_analyzer(self):
        analyzer = SETImpactAnalyzer(self.g)
        report = analyzer.impact_report()
        self.assertIn("score", report)

    def test_pert_planning(self):
        total_days, cp, tasks = get_setp_phase2_planning()
        self.assertTrue(total_days > 0)
        self.assertTrue(len(cp) > 0)

    def test_nash_solver(self):
        ns = NashSolver()
        nash = ns.find_nash()
        self.assertIsNotNone(nash)
        
if __name__ == '__main__':
    unittest.main()
