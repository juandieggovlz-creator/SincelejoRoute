"""
analysis/tree_benchmark.py — Módulo P05
Tree Benchmark Comparativo — SincelejoRoute v2

Compara tiempos de inserción y búsqueda empírica de AVL, B-Tree y B+ Tree
con tamaños de 20, 200 y 2000 elementos.
"""

import time
import random
from modulo_A.trees.avl import AVLTree
from modulo_A.trees.b_tree import BTree
from modulo_A.trees.b_plus_tree import BPlusTree, Route
from modulo_B.graph.graph import Node, Edge

class TreeBenchmark:
    """
    Clase para ejecutar el benchmark comparativo de estructuras de árbol.
    """

    @staticmethod
    def run_benchmark():
        sizes = [20, 200, 2000]
        results = {}

        # Nodo e hilo ficticio para inserciones
        dummy_node = Node("N99", "Dummy Node", "setp", 9.3, -75.3, True)
        dummy_edge = Edge("N99", 5, 300, True)
        dummy_route = Route("N00", "N01", ["N00", "N01"], 5, True)

        for size in sizes:
            results[size] = {
                'avl': {'insert': 0.0, 'search': 0.0, 'height': 0},
                'btree': {'insert': 0.0, 'search': 0.0, 'height': 0},
                'bplus': {'insert': 0.0, 'search': 0.0, 'height': 0}
            }

            # 1. Preparar datos
            # Claves para AVL (strings) y para B/B+ (enteros)
            avl_keys = [f"Location_{i}" for i in range(size)]
            tree_keys = list(range(size))
            
            # Mezclar para que las inserciones no sean ordenadas (caso promedio)
            random.seed(42)
            zip_keys = list(zip(avl_keys, tree_keys))
            random.shuffle(zip_keys)

            avl = AVLTree()
            btree = BTree(t=3)
            bplus = BPlusTree(m=4)

            # --- AVL BENCHMARK ---
            # Inserción
            t0 = time.perf_counter()
            for a_k, _ in zip_keys:
                avl.insert(a_k, dummy_node)
            results[size]['avl']['insert'] = (time.perf_counter() - t0) * 1000
            # Altura
            results[size]['avl']['height'] = avl._root.height if avl._root else 0
            # Búsqueda (100 búsquedas aleatorias)
            t0 = time.perf_counter()
            for _ in range(100):
                target = random.choice(avl_keys)
                _ = avl.search(target)
            results[size]['avl']['search'] = ((time.perf_counter() - t0) * 1000) / 100

            # --- B-TREE BENCHMARK ---
            # Inserción
            t0 = time.perf_counter()
            for _, t_k in zip_keys:
                btree.insert(t_k, dummy_edge)
            results[size]['btree']['insert'] = (time.perf_counter() - t0) * 1000
            # Altura
            results[size]['btree']['height'] = btree.height()
            # Búsqueda (100 búsquedas aleatorias)
            t0 = time.perf_counter()
            for _ in range(100):
                target = random.choice(tree_keys)
                _ = btree.search(target)
            results[size]['btree']['search'] = ((time.perf_counter() - t0) * 1000) / 100

            # --- B+ TREE BENCHMARK ---
            # Inserción
            t0 = time.perf_counter()
            for _, t_k in zip_keys:
                bplus.insert(t_k, dummy_route)
            results[size]['bplus']['insert'] = (time.perf_counter() - t0) * 1000
            # Altura
            results[size]['bplus']['height'] = bplus.height()
            # Búsqueda (100 búsquedas aleatorias)
            t0 = time.perf_counter()
            for _ in range(100):
                target = random.choice(tree_keys)
                _ = bplus.search(target)
            results[size]['bplus']['search'] = ((time.perf_counter() - t0) * 1000) / 100

        return results

    @staticmethod
    def get_report_text(results):
        rep = []
        rep.append("=========================================================================")
        rep.append("  Reporte Comparativo de Estructuras de Árbol (P05) — TreeBenchmark")
        rep.append("=========================================================================")
        rep.append(f"  {'Estructura':<12} {'Tamaño N':<8} {'Inserción (ms)':<16} {'Búsqueda (ms)':<16} {'Altura':<8}")
        rep.append(f"  {'─'*12} {'─'*8} {'─'*16} {'─'*16} {'─'*8}")

        for size in [20, 200, 2000]:
            for name, key in [('AVL Tree', 'avl'), ('B-Tree (t=3)', 'btree'), ('B+ Tree (m=4)', 'bplus')]:
                data = results[size][key]
                rep.append(f"  {name:<12} {size:<8d} {data['insert']:<16.4f} {data['search']:<16.4f} {data['height']:<8d}")
            rep.append(f"  {'─'*65}")

        rep.append("\n  [ANÁLISIS TEÓRICO DE COMPLEJIDAD]")
        rep.append("  - AVL Tree: Inserción O(log n), Búsqueda O(log n). Altura balanceada estricta.")
        rep.append("  - B-Tree  : Inserción O(log_t n), Búsqueda O(log_t n). Menor altura, más claves por nodo.")
        rep.append("  - B+ Tree : Inserción O(log_m n), Búsqueda O(log_m n). Hojas enlazadas (óptimo para rangos).")
        rep.append("\n  [RECOMENDACIÓN DE DISEÑO PARA EL ÍNDICE DEL PROYECTO]")
        rep.append("  1. Para búsquedas exactas por nombre en la CLI (ej. 'UAJS Sede C' -> Node):")
        rep.append("     Se recomienda usar AVL Tree. Los strings no se prestan a ordenamiento secuencial")
        rep.append("     frecuente y el AVL ofrece tiempos constantes O(log n) muy estables en memoria primaria.")
        rep.append("  2. Para indexación de rutas en rangos de tiempo (ej. rutas de 0 a 10 min):")
        rep.append("     Se recomienda usar B+ Tree. Al tener las hojas enlazadas, evita el costo de")
        rep.append("     hacer múltiples búsquedas individuales o recorridos in-order ineficientes.")
        rep.append("=========================================================================")
        
        return "\n".join(rep)
