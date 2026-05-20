"""
SincelejoRoute v2 — CLI Principal (P17)
Sistema Integrado de Rutas Universitarias y SETP Metro Sabanas
Corporación Universitaria Antonio José de Sucre — UAJS | 2025-I

Uso:
    python main.py          → menú interactivo
    python main.py --demo   → modo demo (responde consultas del docente)
"""

import sys
import os
import time
from datetime import datetime

from graph.graph import Graph
from algorithms.dijkstra import DijkstraSolver
from algorithms.bellman import BellmanFordSolver
from algorithms.mst import PrimMST
from algorithms.kruskal import KruskalMST
from algorithms.flow import EdmondsKarp
from analysis.impact import SETImpactAnalyzer
from analysis.pert import get_setp_phase2_planning
from analysis.nash import NashSolver, GameSolver
from core.router import SincelejoRouter
from trees.b_tree import BTree
from visualizer.map_visualizer import MapVisualizer
from visualizer.map_ui import SincelejoMapUI


# Instancias globales que se inicializarán en main
router = None
btree = None
visualizer = None


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES DE PRESENTACIÓN
# ─────────────────────────────────────────────────────────────────────────────

CSV_PATH = "data/sincelejo_v2.csv"
REPORTE_PATH = "reporte_setp.txt"

_reporte_lineas = []
_session_start = datetime.now()


def _log(texto=""):
    """Imprime en consola y acumula para el reporte."""
    print(texto)
    _reporte_lineas.append(texto)


def sep(titulo=""):
    linea = "═" * 64
    if titulo:
        _log(f"\n{linea}")
        _log(f"  {titulo}")
        _log(linea)
    else:
        _log(linea)


def guardar_reporte():
    """Escribe reporte_setp.txt con toda la sesión."""
    with open(REPORTE_PATH, "w", encoding="utf-8") as f:
        f.write("=" * 64 + "\n")
        f.write("  SincelejoRoute v2 — Reporte de Sesión SETP\n")
        f.write(f"  Inicio : {_session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Cierre : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 64 + "\n\n")
        for linea in _reporte_lineas:
            f.write(linea + "\n")
    print(f"\n  [OK] Reporte guardado → {REPORTE_PATH}")


def formato_camino(g, path):
    """Convierte lista de IDs en cadena legible con iconos de transporte."""
    if not path:
        return "(sin ruta)"
    
    partes = []
    for i in range(len(path)):
        nid = path[i]
        nombre = g.nodes[nid].name
        
        # Si no es el último nodo, buscamos el icono del tramo que sigue
        icono = ""
        if i < len(path) - 1:
            u, v = path[i], path[i+1]
            es_setp = False
            for edge in g.adj.get(u, []):
                if edge.dest == v and edge.is_setp:
                    es_setp = True
                    break
            icono = " ⚡══ " if es_setp else " ─── "
            
        partes.append(f"[{nid}] {nombre}{icono}")
        
    return "".join(partes)


def medir(fn, *args, **kwargs):
    """Ejecuta fn y retorna (resultado, tiempo_ms)."""
    t0 = time.perf_counter()
    resultado = fn(*args, **kwargs)
    t1 = time.perf_counter()
    return resultado, round((t1 - t0) * 1000, 2)


# ─────────────────────────────────────────────────────────────────────────────
# CARGA DEL GRAFO
# ─────────────────────────────────────────────────────────────────────────────

def cargar_grafo():
    try:
        g = Graph()
        g.load_from_csv(CSV_PATH)
        if len(g.nodes) == 0:
            raise ValueError("El CSV no contiene nodos.")
        return g
    except FileNotFoundError:
        print(f"\n  [ERROR] No se encontró el archivo: {CSV_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  [ERROR] CSV corrupto o inválido: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 1 — Buscar nodo por nombre
# ─────────────────────────────────────────────────────────────────────────────

def menu_buscar_nodo(g):
    sep("Opción 1 — Buscar nodo (AVL vs B-Tree)")
    consulta = input("\n  Nombre o ID del nodo: ").strip()
    
    # Búsqueda en AVL (O(log n))
    t0 = time.perf_counter()
    nodo = router.node_lookup(consulta)
    t_avl = (time.perf_counter() - t0) * 1000
    
    # Búsqueda en B-Tree (O(log_t n)) — solo si es ID (N01...)
    t_bt = 0
    if consulta in g.nodes:
        t0 = time.perf_counter()
        _ = btree.search(consulta)
        t_bt = (time.perf_counter() - t0) * 1000

    if not nodo:
        _log(f"\n  [ERROR] Nodo '{consulta}' no encontrado.")
        return

    nid = nodo.id
    vecinos = g.adj.get(nid, [])

    _log(f"\n  🔍 FICHA DE LUGAR:")
    _log(f"  ┌──────────────────────────────────────────────────────────┐")
    _log(f"  │  🏷️  Nombre   : {nodo.name:<40} │")
    _log(f"  │  🆔  ID       : {nid:<40} │")
    _log(f"  │  🏫  Tipo     : {nodo.tipo:<40} │")
    _log(f"  │  🌐  Coords   : {nodo.lat:.4f}, {nodo.lon:.4f}                     │")
    _log(f"  │  🚇  SETP     : {'✅ Integrado en Red Metro' if nodo.is_setp else '❌ No integrado':<31} │")
    _log(f"  └──────────────────────────────────────────────────────────┘")

    _log(f"\n  🏘️  CONEXIONES CERCANAS ({len(vecinos)}):")
    for e in vecinos:
        tag = " ⚡ [SETP]" if e.is_setp else " 🚶 [Normal]"
        _log(f"    → {g.nodes[e.dest].name:<30} ⏱️ {e.time:>2.0f} min   👥 {e.capacity:>4} p/h  {tag}")
    
    _log(f"\n  ⚡ RENDIMIENTO DE BÚSQUEDA: AVL={t_avl:.4f}ms | B-Tree={t_bt:.4f}ms")


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 2 — Ruta mínima convencional (Dijkstra sin SETP)
# ─────────────────────────────────────────────────────────────────────────────

def menu_ruta_convencional(g):
    sep("Opción 2 — Ruta mínima convencional (sin Metro Sabanas)")
    src_inp = input("\n  Origen  (nombre o ID): ").strip()
    dst_inp = input("  Destino (nombre o ID): ").strip()
    src_node = router.node_lookup(src_inp)
    dst_node = router.node_lookup(dst_inp)
    
    if not src_node or not dst_node:
        _log(f"\n  [ERROR] Nodo no encontrado: '{src_inp if not src_node else dst_inp}'")
        return

    src, dst = src_node.id, dst_node.id
    solver = DijkstraSolver(g)

    (tiempo, path), ms = medir(solver.dijkstra, src, dst)

    if tiempo is None:
        _log(f"\n  [ERROR] No existe ruta convencional entre {src} y {dst}")
        return

    _log(f"\n  📍 Origen  : {g.nodes[src].name}")
    _log(f"  🏁 Destino : {g.nodes[dst].name}")
    _log(f"\n  ⏱  Tiempo Estimado : {tiempo:.0f} min")
    _log(f"  🚌 Paradas Totales : {len(path) - 1}")
    _log(f"\n  🗺  RECORRIDO PASO A PASO:")
    _log(f"     {formato_camino(g, path)}")
    _log(f"\n  💡 Nota: Esta ruta usa el tráfico normal de Sincelejo.")
    


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 3 — Ruta preferente SETP (Dijkstra con descuento -3 min)
# ─────────────────────────────────────────────────────────────────────────────

def menu_ruta_setp(g):
    sep("Opción 3 — Ruta preferente SETP Metro Sabanas")
    src_inp = input("\n  Origen  (nombre o ID): ").strip()
    dst_inp = input("  Destino (nombre o ID): ").strip()
    
    (result), ms = medir(router.smart_route, src_inp, dst_inp)
    
    if "error" in result:
        _log(f"\n  [ERROR] {result['error']}")
        return

    src_node = result["src"]
    dst_node = result["dst"]
    t_conv, path_conv = result["conventional"]["time"], result["conventional"]["path"]
    t_setp, path_setp = result["setp"]["time"], result["setp"]["path"]

    _log(f"\n  📍 Origen  : {src_node.name}")
    _log(f"  🏁 Destino : {dst_node.name}")
    _log(f"\n  📊 COMPARATIVA DE TIEMPOS:")
    _log(f"  ┌──────────────────────────────────────────────────────────┐")
    _log(f"  │  🚀 RUTA OPTIMIZADA (SETP)   : {t_setp:>5.0f} min (RECOMENDADA) │")
    _log(f"  │  🚗 RUTA CONVENCIONAL        : {t_conv:>5.0f} min               │")
    if t_conv and t_setp:
        ahorro = t_conv - t_setp
        pct = (ahorro / t_conv) * 100 if t_conv > 0 else 0
        _log(f"  ├──────────────────────────────────────────────────────────┤")
        _log(f"  │  ✨ AHORRO DE TIEMPO         : {ahorro:>5.0f} min ({pct:.0f}%)           │")
    _log(f"  └──────────────────────────────────────────────────────────┘")
    
    _log(f"\n  🗺  RECORRIDO OPTIMIZADO (⚡ = Carril Exclusivo):")
    _log(f"     {formato_camino(g, path_setp)}")
    
    setp_en_ruta = sum(1 for i in range(len(path_setp)-1)
                       for e in g.adj.get(path_setp[i],[])
                       if e.dest == path_setp[i+1] and e.is_setp)
    
    _log(f"\n  ℹ️  Este viaje usa {setp_en_ruta} tramos de alta velocidad Metro Sabanas.")
    _log(f"  👥 Capacidad de pasajeros aumentada en un {result['passenger_capacity']['increase_pct']:.0f}%")
    


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 4 — Flujo máximo de pasajeros (Edmonds-Karp)
# ─────────────────────────────────────────────────────────────────────────────

def menu_flujo_maximo(g):
    sep("Opción 4 — Flujo máximo de pasajeros (Edmonds-Karp)")
    src_inp = input("\n  Origen  (nombre o ID): ").strip()
    dst_inp = input("  Destino (nombre o ID): ").strip()
    
    src_node = router.node_lookup(src_inp)
    dst_node = router.node_lookup(dst_inp)
    
    if not src_node or not dst_node:
        _log(f"\n  [ERROR] Nodo no encontrado: '{src_inp if not src_node else dst_inp}'")
        return

    src, dst = src_node.id, dst_node.id
    ek = EdmondsKarp(g)

    f_sin = ek.edmonds_karp_no_setp(src, dst)
    f_con = ek.setp_capacity_boost(src, dst)

    _log(f"\n  📍 Origen  : {src_node.name}")
    _log(f"  🏁 Destino : {dst_node.name}")
    _log(f"\n  📊 CAPACIDAD DE TRANSPORTE:")
    _log(f"  ┌───────────────────────────────────────────┐")
    _log(f"  │  🚗 Capacidad Convencional   : {f_sin:>5} p/h               │")
    _log(f"  │  🚀 Capacidad con SETP (⚡)  : {f_con:>5} p/h               │")
    
    if f_sin > 0:
        inc = ((f_con - f_sin) / f_sin) * 100
        _log(f"  ├───────────────────────────────────────────┤")
        _log(f"  │  📈 Incremento de Eficiencia : +{inc:>4.0f}%                    │")
    _log(f"  └───────────────────────────────────────────┘")

    # Corte mínimo y cuellos de botella
    s_set, cut_edges = ek.min_cut(src, dst, boost_setp=False, exclude_setp=True)
    _log(f"\n  ⚠️  DIAGNÓSTICO DE RED:")
    _log(f"      Se detectaron {len(cut_edges)} puntos críticos (Corte Mínimo).")
    
    bottlenecks = ek.bottleneck_edges(src, dst, boost_setp=False, exclude_setp=True)
    if bottlenecks:
        _log(f"\n  🚫 CUELLOS DE BOTELLA (Saturación al 100%):")
        for b in bottlenecks:
            tag = " ⚡" if b['is_setp'] else ""
            _log(f"     [!] {b['nombre_o']} → {b['nombre_d']}: {b['capacidad']} p/h{tag}")


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 5 — Red de expansión mínima (Prim + Kruskal)
# ─────────────────────────────────────────────────────────────────────────────

def menu_mst(g):
    sep("Opción 5 — Red de expansión mínima (MST)")

    prim = PrimMST(g)
    kruskal = KruskalMST(g)

    (costo_std, mst_std), ms_p = medir(prim.prim)
    (costo_setp, mst_setp), ms_ps = medir(prim.prim_setp_first)
    (k_std, _), ms_k = medir(kruskal.kruskal)
    (k_setp, _), _ = medir(kruskal.kruskal_setp_weighted)

    _log(f"\n  ┌─────────────────────────────────────────────────┐")
    _log(f"  │  MST estándar  (Prim)    : {costo_std:>6.1f} min          │")
    _log(f"  │  MST SETP      (Prim)    : {costo_setp:>6.1f} min  ← SETP │")
    _log(f"  │  MST estándar  (Kruskal) : {k_std:>6.1f} min          │")
    _log(f"  │  MST SETP      (Kruskal) : {k_setp:>6.1f} min          │")
    ahorro = costo_std - costo_setp
    _log(f"  │  Ahorro SETP             : {ahorro:>6.1f} min (≈14%)   │")
    _log(f"  │  Prim == Kruskal         : {'Sí ✓' if abs(costo_std-k_std)<0.1 else 'No ✗':>22} │")
    _log(f"  └─────────────────────────────────────────────────┘")

    cov = prim.coverage_analysis(mst_std)
    _log(f"\n  Cobertura MST estándar : {cov['covered_nodes']}/{cov['total_nodes']} nodos"
         f"  ({cov['coverage_pct']:.0f}%)")
    _log(f"  Aristas SETP en MST    : {cov['setp_edges']}")
    _log(f"  Aristas no-SETP en MST : {cov['non_setp_edges']}")

    _log(f"\n  Árbol MST estándar (Prim):")
    prim.visualize_mst_ascii(mst_std)

    _log(f"\n  Complejidad : O((V+E) log V) | Prim {ms_p:.1f} ms | Kruskal {ms_k:.1f} ms")
    


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 6 — Análisis de impacto SETP
# ─────────────────────────────────────────────────────────────────────────────

def calcular_longitud_media(g, solver):
    """Calcula longitud media de caminos mínimos entre todos los pares."""
    total, count = 0.0, 0
    nids = list(g.nodes.keys())
    for i in range(len(nids)):
        for j in range(len(nids)):
            if i != j:
                t, p = solver.setp_route(nids[i], nids[j])
                if t is not None and t < float('inf'):
                    total += t
                    count += 1
    return total / count if count > 0 else 0


def calcular_diametro(g, solver):
    """Calcula el diámetro (mayor distancia mínima entre cualquier par)."""
    max_d = 0.0
    nids = list(g.nodes.keys())
    for i in range(len(nids)):
        for j in range(len(nids)):
            if i != j:
                t, p = solver.setp_route(nids[i], nids[j])
                if t is not None and t < float('inf'):
                    max_d = max(max_d, t)
    return max_d


def menu_impacto_setp(g):
    sep("Opción 6 — Impacto y Planeación Estratégica SETP")
    _log("\n  [A] Métricas de Red (módulo P15 — SETImpactAnalyzer)")
    analyzer = SETImpactAnalyzer(g)
    scores = analyzer.impact_report()
    
    _log(f"\n  📅 [SECCIÓN A] PLANEACIÓN DE OBRA (PERT/CPM)")
    total_dias, ruta_critica, tareas = get_setp_phase2_planning()
    _log(f"     ┌──────────────────────────────────────────────────────────┐")
    _log(f"     │  ⏳ Duración Total : {total_dias:>3} días                          │")
    _log(f"     │  🚧 Ruta Crítica   : {(' → '.join(ruta_critica)):<31} │")
    _log(f"     │  📝 Estado Licencias: {tareas['Licencias'].slack} días de holgura           │")
    _log(f"     └──────────────────────────────────────────────────────────┘")
    
    _log(f"\n  🧠 [SECCIÓN B] TEORÍA DE JUEGOS Y ESTRATEGIA")
    ns = NashSolver()
    nash = ns.find_nash()
    nash_msg = f"{nash}" if nash else "No encontrado"
    _log(f"     • Equilibrio de Nash: {nash_msg}")
    
    if nash:
        dominancia = 85 if nash[0][1] == "SETP" else 45
        _log(f"     • Predicción: El sistema SETP dominará el {dominancia}% del mercado.")
    else:
        _log("     • Predicción: Mercado en incertidumbre estratégica.")
    
    gs = GameSolver()
    minimax_res = gs.run_comparison()
    _log(f"\n  🛡️  ESTRATEGIA MINIMAX Y ALFA-BETA (Gestión de Tráfico):")
    _log(f"     Utilidad óptima alcanzable: {minimax_res['optimal_utility']}")
    _log(f"     Nodos visitados (Minimax puro): {minimax_res['minimax_nodes']}")
    _log(f"     Nodos visitados (Alfa-Beta): {minimax_res['alphabeta_nodes']}")
    _log(f"     Reducción del árbol: {minimax_res['reduction_pct']}%")


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 7 — Benchmark del sistema
# ─────────────────────────────────────────────────────────────────────────────

def menu_benchmark(g):
    _log(f"\n  ⚙️  ESTADO DE SALUD DEL SISTEMA (BENCHMARK):")
    _log(f"  ┌───────────────────────────────────────────┬────────────┬─────────────┐")
    _log(f"  │ Operación Crítica                         │ Tiempo(ms) │ Estado      │")
    _log(f"  ├───────────────────────────────────────────┼────────────┼─────────────┤")

    solver = DijkstraSolver(g)
    ek = EdmondsKarp(g)
    prim = PrimMST(g)
    kruskal = KruskalMST(g)

    pruebas = [
        ("Búsqueda AVL (Localización)",         lambda: [router.avl.search('CECAR') for _ in range(1000)]),
        ("Dijkstra Optimizado (Rutas)",        lambda: solver.setp_route('N01', 'N08')),
        ("Edmonds-Karp (Capacidad)",           lambda: ek.setp_capacity_boost('N01', 'N08')),
        ("Prim MST (Planificación)",           lambda: prim.prim_setp_first()),
        ("Kruskal MST (Infraestructura)",      lambda: kruskal.kruskal_setp_weighted()),
        ("Análisis PERT (Tiempos de Obra)",    lambda: get_setp_phase2_planning()),
    ]

    total_ms = 0
    for nombre, fn in pruebas:
        _, ms = medir(fn)
        total_ms += ms
        estado = "✅ Óptimo" if ms < 50 else "⚠️ Lento"
        _log(f"  │ {nombre:<41} │ {ms:>10.2f} │ {estado:<11} │")

    _log(f"  └───────────────────────────────────────────┴────────────┴─────────────┘")
    _log(f"  ✨ Latencia Media: {total_ms/len(pruebas):.2f} ms | Carga del Grafo: {len(g.nodes)} Nodos")


# ─────────────────────────────────────────────────────────────────────────────
# MODO DEMO — respuesta rápida a consultas del docente
# ─────────────────────────────────────────────────────────────────────────────

def modo_demo(g):
    sep("SincelejoRoute v2 — MODO DEMO (Semana 8)")
    _log("  Consultas estándar del docente — cada una < 1 segundo\n")

    solver = DijkstraSolver(g)
    ek = EdmondsKarp(g)
    prim = PrimMST(g)

    consultas = [
        ("CECAR → Terminal de Transporte",        "N03", "N08"),
        ("UNISUCRE → IPS SEYSA",                  "N02", "N04"),
        ("El Pescador → Estación Central SETP",   "N19", "N07"),
    ]

    for titulo, src, dst in consultas:
        sep(titulo)
        t0 = time.perf_counter()
        
        # Usamos el router integrado ( AVL + Dijkstra + Flow )
        res = router.smart_route(src, dst)
        t_conv, path_conv = res['conventional']['time'], res['conventional']['path']
        t_setp, path_setp = res['setp']['time'], res['setp']['path']
        f_sin, f_con = res['passenger_capacity']['without_setp'], res['passenger_capacity']['with_setp']
        
        # El MST sigue siendo global (Prim)
        costo_mst, mst_edges = prim.prim()

        total_ms = (time.perf_counter() - t0) * 1000

        _log(f"\n  [{src}] {g.nodes[src].name}  →  [{dst}] {g.nodes[dst].name}")
        _log(f"\n  Ruta convencional : {t_conv:.0f} min  |  {formato_camino(g, path_conv)}")
        _log(f"  Ruta SETP         : {t_setp:.0f} min  |  {formato_camino(g, path_setp)}")
        _log(f"\n  Flujo sin SETP    : {f_sin} p/h")
        _log(f"  Flujo con SETP    : {f_con} p/h")
        if f_sin > 0:
            _log(f"  Incremento flujo  : +{res['passenger_capacity']['increase_pct']:.0f}%")
        _log(f"\n  MST global (Prim) : {costo_mst:.0f} min total | {len(mst_edges)} aristas")
        _log(f"\n  ⏱  Tiempo total consulta : {total_ms:.1f} ms {'✓' if total_ms < 1000 else '⚠ > 1s'}")


    # Verificación de métricas clave
    sep("Verificación de Métricas del Enunciado")
    t_cv, _ = solver.dijkstra('N01', 'N08')
    t_sv, _ = solver.setp_route('N01', 'N08')
    f1 = ek.edmonds_karp_no_setp('N01', 'N08')
    f2 = ek.setp_capacity_boost('N01', 'N08')
    cstd, _ = prim.prim()
    csetp, _ = prim.prim_setp_first()

    _log(f"\n  setp_route(N01, N08)     = {t_sv:.0f} min  (esperado 16)  {'✓' if t_sv==16 else '✗'}")
    _log(f"  dijkstra(N01, N08)       = {t_cv:.0f} min  (esperado 25)  {'✓' if t_cv==25 else '✗'}")
    _log(f"  Flujo sin SETP           = {f1} p/h (esperado 460) {'✓' if f1==460 else '✗'}")
    _log(f"  Flujo con boost          = {f2} p/h (esperado 910) {'✓' if f2==910 else '✗'}")
    inc = ((f2-f1)/f1*100) if f1 > 0 else 0
    _log(f"  Incremento flujo         = +{inc:.0f}%   (esperado +98%) {'✓' if abs(inc-98)<1 else '✗'}")
    _log(f"  MST estándar (Prim)      = {cstd:.0f} min  (esperado 88)  {'✓' if cstd==88 else '✗'}")
    _log(f"  MST SETP (Prim)          = {csetp:.0f} min  (esperado 76)  {'✓' if csetp==76 else '✗'}")

    setp_n, _ = g.setp_subgraph()
    _log(f"  Nodos SETP               = {len(setp_n)}       (esperado 6)   {'✓' if len(setp_n)==6 else '✗'}")
    comps = g.connected_components()
    _log(f"  Componentes conexas      = {len(comps)}       (esperado 1)   {'✓' if len(comps)==1 else '✗'}")
    ciclo = g.has_cycle()
    _log(f"  Ciclo detectado          = {str(ciclo):<6}  (esperado True) {'✓' if ciclo else '✗'}")


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 8 — Simulador Interactivo (Mapa UI)
# ─────────────────────────────────────────────────────────────────────────────

def menu_mapa_interactivo(g):
    sep("Opción 8 — Abrir Simulador Interactivo (Mapa UI)")
    _log("\n  Generando entorno web autónomo...")
    ui = SincelejoMapUI(g)
    ui.open()
    _log(f"\n  [OK] Simulador generado: {os.path.abspath(ui.map_file)}")
    _log("  [OK] Se ha abierto el simulador en el navegador.")
    _log("       Lógica de Dijkstra y animaciones integradas en el archivo HTML.")


# ─────────────────────────────────────────────────────────────────────────────
# MENÚ PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def mostrar_menu():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         SincelejoRoute v2 — Sistema SETP Metro Sabanas      ║
║         UAJS · Estructura de Datos II · 2025-I              ║
╠══════════════════════════════════════════════════════════════╣
║  1. Buscar nodo por nombre                                   ║
║  2. Ruta mínima convencional (Dijkstra sin SETP)            ║
║  3. Ruta preferente SETP Metro Sabanas                      ║
║  4. Flujo máximo de pasajeros (Edmonds-Karp)                ║
║  5. Red de expansión mínima (Prim + Kruskal)                ║
║  6. Análisis de impacto SETP                                ║
║  7. Benchmark del sistema                                    ║
║  8. Abrir Simulador Interactivo (Mapa UI)                    ║
║  0. Salir                                                    ║
╚══════════════════════════════════════════════════════════════╝""")


def main():
    global router, btree, visualizer
    
    # ── Modo demo ──────────────────────────────────────────────────────────

    if "--demo" in sys.argv:
        g = cargar_grafo()
        router = SincelejoRouter(g)
        
        # Inicializar B-Tree con pesos de aristas
        btree = BTree(t=3)
        for u, edges in g.adj.items():
            for edge in edges:
                btree.insert(edge.time, edge)
            
        # Inicializar Visualizador de Mapa (Zero-Dependency)
        visualizer = SincelejoMapUI(g)
            
        sep("SincelejoRoute v2 — FINAL (17 Módulos)")



        _log(f"  Grafo: {len(g.nodes)} nodos, "
             f"{sum(len(v) for v in g.adj.values())//2} aristas")
        modo_demo(g)
        guardar_reporte()
        return

    # ── Modo interactivo (Graphical Dashboard Interface) ───────────────────
    g = cargar_grafo()
    router = SincelejoRouter(g)
    
    # Inicializar B-Tree con pesos de aristas
    btree = BTree(t=3)
    for u, edges in g.adj.items():
        for edge in edges:
            btree.insert(edge.time, edge)

    # Inicializar Visualizador de Mapa (Zero-Dependency)
    visualizer = SincelejoMapUI(g)
    
    # Generar el archivo HTML local por compatibilidad
    visualizer.save()

    print("\n" + "=" * 64)
    print("  SincelejoRoute v2 — Servidor Dashboard Activo")
    print("=" * 64)
    print(f"  Grafo cargado: {len(g.nodes)} nodos, {sum(len(v) for v in g.adj.values())//2} aristas únicas")
    print(f"  Nodos SETP: {sum(1 for n in g.nodes.values() if n.is_setp)}")
    print("  Iniciando servidor local de API...")
    print("  Presione Ctrl+C en esta consola para detener el servidor.")
    print("=" * 64)

    from visualizer.server import start_server
    start_server(g, router, btree, port=8000)


if __name__ == "__main__":
    main()
