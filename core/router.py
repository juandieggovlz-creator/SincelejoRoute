"""
core/router.py — Módulo P16
SincelejoRoute Router Core — Integrating AVL & Graphs

This module acts as the "brain" of the system, connecting:
  - AVL Tree: For O(log n) node searching by name.
  - Dijkstra/Bellman-Ford: For pathfinding.

Functions:
  - node_lookup(query): Finds a Node object given a name or ID string.
  - smart_route(src_query, dst_query): Calculates and compares the best routes.
"""

from graph.graph import Graph, Node
from trees.avl import AVLTree
from algorithms.dijkstra import DijkstraSolver
from algorithms.flow import EdmondsKarp

class SincelejoRouter:
    """
    SincelejoRouter connects the data structures (AVL) and algorithms (Graphs).
    """

    def __init__(self, graph: Graph):
        self.graph = graph
        self.avl = AVLTree()
        self.dijkstra = DijkstraSolver(graph)
        self.flow = EdmondsKarp(graph)

        # Index all nodes in the AVL tree for fast lookup by name
        for node in graph.nodes.values():
            self.avl.insert(node.name, node)

    def node_lookup(self, query: str) -> Node:
        """
        Fast node lookup using ID or AVL Tree (Name).
        
        1. Checks if query is a direct ID (e.g., "N01").
        2. Searches the AVL tree for an exact name match.
        3. Searches for a partial name match.
        """
        query = query.strip()
        
        # 1. ID Lookup
        if query in self.graph.nodes:
            return self.graph.nodes[query]
            
        # 2. Exact Name Lookup (AVL)
        node = self.avl.search(query)
        if node:
            return node
            
        # 3. Partial Name Lookup
        results = self.avl.search_partial(query)
        if results:
            return results[0] # Return the first closest match
            
        return None

    def smart_route(self, src_query: str, dst_query: str):
        """
        Intelligent routing that compares conventional vs SETP routes.
        
        Returns a dictionary with:
          - source/dest nodes
          - conventional_time/path
          - setp_time/path
          - time_saved
          - flow_no_setp / flow_with_setp
        """
        src_node = self.node_lookup(src_query)
        dst_node = self.node_lookup(dst_query)
        
        if not src_node or not dst_node:
            return {
                "error": "One or both nodes not found.",
                "src_missing": src_node is None,
                "dst_missing": dst_node is None
            }

        # Calculate Dijkstra routes
        conv_time, conv_path = self.dijkstra.dijkstra(src_node.id, dst_node.id)
        setp_time, setp_path = self.dijkstra.setp_route(src_node.id, dst_node.id)
        
        # Calculate Flow (optional but useful for integration)
        f_sin = self.flow.edmonds_karp_no_setp(src_node.id, dst_node.id)
        f_con = self.flow.setp_capacity_boost(src_node.id, dst_node.id)

        return {
            "src": src_node,
            "dst": dst_node,
            "conventional": {
                "time": conv_time,
                "path": conv_path
            },
            "setp": {
                "time": setp_time,
                "path": setp_path
            },
            "time_saved": (conv_time - setp_time) if conv_time and setp_time else 0,
            "passenger_capacity": {
                "without_setp": f_sin,
                "with_setp": f_con,
                "increase_pct": ((f_con - f_sin) / f_sin * 100) if f_sin > 0 else 0
            }
        }
