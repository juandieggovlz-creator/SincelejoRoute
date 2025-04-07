import unittest
import os
from modulo_B.graph.graph import Graph, Node
from modulo_B.algorithms.dijkstra import DijkstraSolver
from modulo_B.algorithms.flow import EdmondsKarp

class TestModuloB(unittest.TestCase):
    def setUp(self):
        self.g = Graph()
        # Load from the real dataset to test realistic scenarios
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sincelejo_v2.csv")
        self.g.load_from_csv(csv_path)
        
    def test_graph_add_nodes(self):
        self.assertIn("N01", self.g.nodes)
        self.assertTrue(len(self.g.nodes) > 0)

    def test_dijkstra_shortest_path(self):
        solver = DijkstraSolver(self.g)
        tiempo, path = solver.dijkstra("N01", "N08")
        self.assertIsNotNone(tiempo)
        self.assertTrue(len(path) > 0)

    def test_edmonds_karp_flow(self):
        ek = EdmondsKarp(self.g)
        flow = ek.edmonds_karp_no_setp("N01", "N08")
        self.assertTrue(flow > 0)

if __name__ == '__main__':
    unittest.main()
