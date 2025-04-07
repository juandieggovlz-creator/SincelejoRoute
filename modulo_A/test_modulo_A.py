import unittest
from modulo_A.trees.avl import AVLTree
from modulo_B.graph.graph import Node
from modulo_A.trees.b_tree import BTree
from modulo_A.trees.b_plus_tree import BPlusTree, Route

class TestModuloA(unittest.TestCase):
    def test_avl_insertion_and_search(self):
        avl = AVLTree()
        avl.insert("N01", Node("N01", "Node1", "Tipo1", 0.0, 0.0, False))
        avl.insert("N02", Node("N02", "Node2", "Tipo2", 1.0, 1.0, True))
        
        node = avl.search("N01")
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "Node1")

    def test_btree_insertion(self):
        bt = BTree(t=2)
        bt.insert(10, "Route10")
        bt.insert(20, "Route20")
        bt.insert(5, "Route5")
        
        res = bt.search(10)
        self.assertIsNotNone(res)
        self.assertIn("Route10", res)

    def test_b_plus_tree_range_search(self):
        bpt = BPlusTree(m=3)
        bpt.insert(15, Route("N01", "N02", ["N01", "N02"], 15, True))
        bpt.insert(20, Route("N01", "N03", ["N01", "N03"], 20, False))
        bpt.insert(10, Route("N01", "N04", ["N01", "N04"], 10, True))

        results = bpt.rangeSearch(10, 15)
        self.assertEqual(len(results), 2)
        costs = [r.costo for r in results]
        self.assertIn(10, costs)
        self.assertIn(15, costs)

if __name__ == '__main__':
    unittest.main()
