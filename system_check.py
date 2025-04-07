"""
system_check.py — Validador Integral del Proyecto SincelejoRoute
Versión: 1.0 ( UAJS 2025-I )

Este script verifica la integridad de las 11 fases del proyecto, desde la
consistencia del CSV hasta la generación del mapa interactivo y el benchmark.
"""

import sys
import os
import time
import json
from datetime import datetime

# --- Imports de los módulos del proyecto ---
try:
    from modulo_B.graph.graph import Graph
    from modulo_B.algorithms.dijkstra import DijkstraSolver
    from modulo_B.algorithms.mst import PrimMST
    from modulo_B.algorithms.kruskal import KruskalMST
    from modulo_B.algorithms.flow import EdmondsKarp
    from modulo_A.core.router import SincelejoRouter
    from modulo_A.trees.avl import AVLTree
    from modulo_C.visualizer.map_ui import SincelejoMapUI
    from modulo_C.analysis.impact import SETImpactAnalyzer
except ImportError as e:
    print(f"\n[ERROR] No se pudo importar un módulo crítico: {e}")
    sys.exit(1)

# Estructura para almacenar resultados
results = {
    "CSV": "FAIL",
    "Graph": "FAIL",
    "BFS/DFS": "FAIL",
    "Dijkstra": "FAIL",
    "Dijkstra SETP": "FAIL",
    "MST": "FAIL",
    "Flow": "FAIL",
    "AVL": "FAIL",
    "Map": "FAIL",
    "UI": "FAIL",
    "Integration": "FAIL"
}

errors = []

def log_error(module, desc):
    errors.append(f"ERROR en {module}: {desc}")

def benchmark(fn, *args, **kwargs):
    t0 = time.perf_counter()
    res = fn(*args, **kwargs)
    t1 = time.perf_counter()
    return res, (t1 - t0) * 1000

def run_checks():
    global results
    
    # 1. VALIDACIÓN CSV
    csv_path = "data/sincelejo_v2.csv"
    if not os.path.exists(csv_path):
        log_error("CSV", "Archivo data/sincelejo_v2.csv no encontrado.")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "NODES" not in content or "EDGES" not in content:
        log_error("CSV", "Estructura inválida. Faltan secciones NODES/EDGES.")
        return
    
    results["CSV"] = "OK"

    # 2. VALIDACIÓN GRAFO & CARGA
    g = Graph()
    _, load_time = benchmark(g.load_from_csv, csv_path)
    
    if len(g.nodes) != 20:
        log_error("Graph", f"Se esperaban 20 nodos, se cargaron {len(g.nodes)}.")
    elif sum(len(adj) for adj in g.adj.values()) // 2 < 30: # 34 aristas approx
        log_error("Graph", "Conteo de aristas inferior al esperado.")
    else:
        setp_nodes = sum(1 for n in g.nodes.values() if n.is_setp)
        if setp_nodes != 6:
            log_error("Graph", f"Se esperaban 6 nodos SETP, se encontraron {setp_nodes}.")
        else:
            results["Graph"] = "OK"

    # 3. VALIDACIÓN BFS / DFS
    visited_bfs = g.bfs('N01')
    discovery_dfs, finish_dfs = g.dfs('N01')
    if len(visited_bfs) == 20 and len(discovery_dfs) == 20:
        results["BFS/DFS"] = "OK"
    else:
        log_error("BFS/DFS", f"Grafo no conexo. Visitados BFS: {len(visited_bfs)}, DFS: {len(discovery_dfs)}")


    # 4. VALIDACIÓN DIJKSTRA
    solver = DijkstraSolver(g)
    (tiempo, path), t_dijkstra = benchmark(solver.dijkstra, 'N01', 'N08')
    if tiempo is not None and tiempo > 0 and len(path) > 0:
        results["Dijkstra"] = "OK"
    else:
        log_error("Dijkstra", "Ruta N01-N08 no encontrada.")

    # 5. VALIDACIÓN DIJKSTRA SETP
    (tiempo_setp, path_setp), _ = benchmark(solver.setp_route, 'N01', 'N08')
    if tiempo_setp is not None and tiempo_setp <= tiempo:
        results["Dijkstra SETP"] = "OK"
    else:
        log_error("Dijkstra SETP", "Ruta SETP más lenta o no encontrada.")

    # 6. VALIDACIÓN MST
    prim = PrimMST(g)
    kruskal = KruskalMST(g)
    (cost_p, edges_p), t_mst = benchmark(prim.prim)
    (cost_k, _), _ = benchmark(kruskal.kruskal)
    
    if abs(cost_p - cost_k) < 0.1 and len(edges_p) == 19:
        results["MST"] = "OK"
    else:
        log_error("MST", f"Costos inconsistentes: Prim {cost_p} vs Kruskal {cost_k}")

    # 7. VALIDACIÓN FLUJO MÁXIMO
    ek = EdmondsKarp(g)
    f_sin, t_flow = benchmark(ek.edmonds_karp_no_setp, 'N01', 'N08')
    f_con, _ = benchmark(ek.setp_capacity_boost, 'N01', 'N08')
    if f_sin > 0 and f_con > f_sin:
        results["Flow"] = "OK"
    else:
        log_error("Flow", f"Flujo inválido: SinSETP={f_sin}, ConSETP={f_con}")

    # 8. VALIDACIÓN AVL
    avl = AVLTree()
    for nid, node in g.nodes.items():
        avl.insert(nid, node)
    search_res = avl.search('N07')
    if search_res and search_res.id == 'N07':
        results["AVL"] = "OK"
    else:
        log_error("AVL", "Búsqueda en árbol AVL falló.")

    # 9. VALIDACIÓN MAPA & UI
    try:
        from modulo_C.visualizer.map_ui import SincelejoMapUI, HAS_FOLIUM
        ui = SincelejoMapUI(g)
        html = ui.generate_html()
        
        if len(html) > 5000: # El HTML mínimo con Leaflet y datos es ~10KB
            results["Map"] = "OK"
            
            # Verificar elementos clave de la UI
            if "sidebar" in html and "select" in html and "calculate" in html:
                results["UI"] = "OK"
            else:
                log_error("UI", "Elementos de la interfaz lateral no encontrados en HTML.")
            
            # Verificar datos del grafo
            if "graphData" in html and "N07" in html:
                pass # OK
            else:
                log_error("Map", "Datos del grafo no inyectados en HTML.")
        else:
            log_error("Map", "El HTML generado está vacío o es demasiado corto.")
            
    except Exception as e:
        log_error("Map/UI", f"Error en validación visual: {e}")



    # 10. INTEGRACIÓN (Router Core)
    router = SincelejoRouter(g)
    res_int = router.smart_route('N01', 'N08')
    if "conventional" in res_int and "setp" in res_int:
        results["Integration"] = "OK"
    else:
        log_error("Integration", "Router core falló en consulta smart_route.")

    # 11. BENCHMARK FINAL
    print("\nBENCHMARK DEL SISTEMA")
    print("-" * 32)
    print(f"Carga Grafo   : {load_time:>10.2f} ms")
    print(f"Dijkstra      : {t_dijkstra:>10.2f} ms")
    print(f"MST (Prim)    : {t_mst:>10.2f} ms")
    print(f"Flujo Máximo  : {t_flow:>10.2f} ms")
    
    all_fast = all(t < 1000 for t in [load_time, t_dijkstra, t_mst, t_flow])
    if not all_fast:
        log_error("Benchmark", "Alguna operación superó el segundo de ejecución.")

    # REPORTE FINAL
    print("\n" + "=" * 32)
    print("  SINCELEJOROUTE SYSTEM CHECK")
    print("=" * 32 + "\n")
    
    for mod, res in results.items():
        print(f"{mod:<15}: {res}")
    
    if all(r == "OK" for r in results.values()):
        print("\nSYSTEM STATUS: 100% FUNCTIONAL")
    else:
        print("\nSYSTEM STATUS: FAILURES DETECTED")
        print("\nDETALLES DE ERRORES:")
        for err in errors:
            print(f"  - {err}")

if __name__ == "__main__":
    run_checks()
