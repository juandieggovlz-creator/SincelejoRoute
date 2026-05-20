"""
analysis/impact.py — Módulo P15
Análisis de impacto SETP Metro Sabanas — SincelejoRoute v2

Compara métricas de teoría de grafos entre:
  v1: red SIN infraestructura SETP (12 nodos, solo corredores convencionales)
  v2: red CON SETP Metro Sabanas activo (20 nodos, rutas priorizadas)

Métricas implementadas:
  - average_path_length()      → longitud media de todos los caminos mínimos
  - network_diameter()         → mayor distancia mínima entre cualquier par
  - clustering_coefficient()   → densidad local de conexiones por nodo
  - setp_benefit_score()       → índice compuesto de mejora SETP
  - impact_report()            → reporte completo con tabla comparativa

Complejidad total: O(V² · (V+E) log V) — dominada por all-pairs Dijkstra.

Referencia del enunciado (P15):
  Ø de 14.2 → 10.2 min (−28%) | diámetro de 38 → 27 min (−29%) | flujo +98%
"""

import time
from graph.graph import Graph
from algorithms.dijkstra import DijkstraSolver
from algorithms.flow import EdmondsKarp

# ─────────────────────────────────────────────────────────────────────────────
# DEFINICIÓN DEL GRAFO V1 (sin SETP)
# V1 = 12 nodos originales antes de la construcción del SETP Metro Sabanas:
#   Universidades: N00, N01, N02, N03
#   Salud/IPS:     N04, N05, N06
#   Movilidad:     N08, N13, N14
#   Comercio:      N16, N17
# Los nodos SETP (N07,N09,N10,N11,N12,N15) y comercio nuevo (N18,N19) son v2.
# ─────────────────────────────────────────────────────────────────────────────
V1_NODES = frozenset({'N00', 'N01', 'N02', 'N03', 'N04', 'N05', 'N06',
                      'N08', 'N13', 'N14', 'N16', 'N17'})


class SETImpactAnalyzer:
    """
    Analizador de impacto SETP para SincelejoRoute.

    Compara la red de movilidad de Sincelejo antes (v1, 12 nodos) y después
    (v2, 20 nodos) de incorporar el SETP Metro Sabanas.

    Parámetros
    ----------
    graph : Graph
        Grafo v2 completo (20 nodos) cargado desde sincelejo_v2.csv.
    """

    def __init__(self, graph: Graph):
        self.graph = graph
        self.solver = DijkstraSolver(graph)
        self.ek = EdmondsKarp(graph)
        self._cache_v1 = None   # all-pairs v1 (dist dict)
        self._cache_v2 = None   # all-pairs v2 (dist dict)

    # ─────────────────────────────────────────────────────────────────────
    # Cache de caminos mínimos (all-pairs Dijkstra)
    # ─────────────────────────────────────────────────────────────────────

    def _all_pairs_v1(self):
        """
        Calcula all-pairs shortest paths sobre los 12 nodos v1
        usando Dijkstra convencional (sin aristas SETP).
        Complejidad: O(V1² · (V+E) log V)
        """
        if self._cache_v1 is not None:
            return self._cache_v1
        result = {}
        for src in V1_NODES:
            for dst in V1_NODES:
                if src != dst:
                    t, _ = self.solver.dijkstra(src, dst)
                    if t is not None and t < float('inf'):
                        result[(src, dst)] = t
        self._cache_v1 = result
        return result

    def _all_pairs_v2(self):
        """
        Calcula all-pairs shortest paths sobre los 20 nodos v2
        usando Dijkstra SETP (con descuento en aristas Metro Sabanas).
        Complejidad: O(V2² · (V+E) log V)
        """
        if self._cache_v2 is not None:
            return self._cache_v2
        result = {}
        nodes = list(self.graph.nodes.keys())
        for src in nodes:
            for dst in nodes:
                if src != dst:
                    t, _ = self.solver.setp_route(src, dst)
                    if t is not None and t < float('inf'):
                        result[(src, dst)] = t
        self._cache_v2 = result
        return result

    # ─────────────────────────────────────────────────────────────────────
    # Métrica 1 — Longitud media de caminos mínimos (Average Path Length)
    # ─────────────────────────────────────────────────────────────────────

    def average_path_length(self, version='v2'):
        """
        Longitud media de todos los caminos mínimos entre pares alcanzables.

        Fórmula:
            Ø = (1 / n(n-1)) · Σ d(u,v)   para todo par (u,v) alcanzable

        Parámetros
        ----------
        version : str
            'v1' = red sin SETP (12 nodos, Dijkstra convencional)
            'v2' = red con SETP (20 nodos, Dijkstra con prioridad SETP)

        Retorna
        -------
        float : longitud media en minutos. 0 si no hay pares alcanzables.
        """
        pairs = self._all_pairs_v1() if version == 'v1' else self._all_pairs_v2()
        if not pairs:
            return 0.0
        return sum(pairs.values()) / len(pairs)

    # ─────────────────────────────────────────────────────────────────────
    # Métrica 2 — Diámetro de la red
    # ─────────────────────────────────────────────────────────────────────

    def network_diameter(self, version='v2'):
        """
        Diámetro de la red: mayor distancia mínima entre cualquier par de nodos.

        Fórmula:
            D = max { d(u,v) : u≠v, d(u,v) < ∞ }

        Parámetros
        ----------
        version : str  — 'v1' o 'v2'

        Retorna
        -------
        float : diámetro en minutos. 0 si el grafo está vacío.
        """
        pairs = self._all_pairs_v1() if version == 'v1' else self._all_pairs_v2()
        if not pairs:
            return 0.0
        return max(pairs.values())

    # ─────────────────────────────────────────────────────────────────────
    # Métrica 3 — Coeficiente de agrupamiento (Clustering Coefficient)
    # ─────────────────────────────────────────────────────────────────────

    def clustering_coefficient(self, node_id=None, version='v2'):
        """
        Coeficiente de agrupamiento local de un nodo (o la media global).

        Para el nodo v con k vecinos:
            C(v) = |{(u,w) ∈ E : u,w ∈ N(v)}| / (k · (k-1))

        Parámetros
        ----------
        node_id : str o None
            ID del nodo. Si es None, retorna el coeficiente medio global.
        version : str
            'v1' considera solo vecinos en V1_NODES.
            'v2' considera todos los vecinos del grafo completo.

        Retorna
        -------
        float : coeficiente de agrupamiento (0.0 a 1.0).
        """
        g = self.graph
        node_set = V1_NODES if version == 'v1' else set(g.nodes.keys())

        def _cc_node(nid):
            neighbors = {e.dest for e in g.adj.get(nid, [])
                         if e.dest in node_set}
            k = len(neighbors)
            if k < 2:
                return 0.0
            links = sum(
                1 for u in neighbors
                for e in g.adj.get(u, [])
                if e.dest in neighbors
            )
            return links / (k * (k - 1))

        if node_id is not None:
            return _cc_node(node_id)

        # Media global
        target_nodes = node_set & set(g.nodes.keys())
        values = [_cc_node(n) for n in target_nodes]
        return sum(values) / len(values) if values else 0.0

    # ─────────────────────────────────────────────────────────────────────
    # Métrica 4 — SETP Benefit Score (índice compuesto)
    # ─────────────────────────────────────────────────────────────────────

    def setp_benefit_score(self):
        """
        Índice compuesto de mejora SETP.

        Combina tres dimensiones de mejora:
          - Δ longitud media de camino   (peso 40%)
          - Δ diámetro de red            (peso 30%)
          - Δ flujo máximo N01→N08       (peso 30%)

        Retorna
        -------
        dict con:
          'score'       : puntaje compuesto (0.0 a 1.0, mayor = mejor SETP)
          'mejora_lm'   : % mejora en longitud media
          'mejora_diam' : % mejora en diámetro
          'mejora_flujo': % mejora en flujo máximo
        """
        lm_v1 = self.average_path_length('v1')
        lm_v2 = self.average_path_length('v2')
        d_v1  = self.network_diameter('v1')
        d_v2  = self.network_diameter('v2')

        f_sin = self.ek.edmonds_karp_no_setp('N01', 'N08')
        f_con = self.ek.setp_capacity_boost('N01', 'N08')

        mejora_lm   = ((lm_v1 - lm_v2) / lm_v1 * 100) if lm_v1 > 0 else 0
        mejora_diam = ((d_v1  - d_v2)  / d_v1  * 100) if d_v1  > 0 else 0
        mejora_flujo= ((f_con  - f_sin) / f_sin  * 100) if f_sin > 0 else 0

        # Normalizar a [0,1]: 28% mejora LM → 0.28, etc.
        score = (mejora_lm * 0.40 + mejora_diam * 0.30 + mejora_flujo * 0.30) / 100

        return {
            'score':        round(score, 4),
            'mejora_lm':    round(mejora_lm,    2),
            'mejora_diam':  round(mejora_diam,  2),
            'mejora_flujo': round(mejora_flujo, 2),
            'lm_v1': round(lm_v1, 2),
            'lm_v2': round(lm_v2, 2),
            'd_v1':  round(d_v1,  1),
            'd_v2':  round(d_v2,  1),
            'f_sin': f_sin,
            'f_con': f_con,
        }

    # ─────────────────────────────────────────────────────────────────────
    # Reporte completo de impacto SETP
    # ─────────────────────────────────────────────────────────────────────

    def impact_report(self):
        """
        Genera y muestra el reporte comparativo v1 vs v2.

        Incluye:
          - Tabla de métricas con valores absolutos y % de mejora
          - Análisis del subgrafo SETP (6 nodos)
          - Coeficientes de agrupamiento por categoría
          - Índice compuesto SETP Benefit Score
          - Validación contra los valores de referencia del enunciado
        """
        g = self.graph
        sep = "═" * 66

        print(f"\n{sep}")
        print("  Análisis de Impacto SETP Metro Sabanas — SincelejoRoute v2")
        print(f"  Módulo P15 | Corporación Universitaria UAJS | 2025-I")
        print(sep)

        t0 = time.perf_counter()

        # ── Calcular todas las métricas ────────────────────────────────
        print("\n  Calculando métricas... ", end="", flush=True)
        scores = self.setp_benefit_score()
        cc_v1  = self.clustering_coefficient(version='v1')
        cc_v2  = self.clustering_coefficient(version='v2')
        print("listo.\n")

        # ── Tabla principal ────────────────────────────────────────────
        print(f"  {'Métrica':<38} {'v1 (sin SETP)':>13} {'v2 (con SETP)':>14} {'Mejora':>8}")
        print(f"  {'─'*38} {'─'*13} {'─'*14} {'─'*8}")

        def fila(nombre, v1, v2, fmt="{:.1f}", unidad=""):
            v1s = fmt.format(v1) + unidad
            v2s = fmt.format(v2) + unidad
            if v1 > 0:
                pct = ((v1 - v2) / v1) * 100
                pcts = f"−{pct:.0f}%" if pct > 0 else f"+{-pct:.0f}%"
            else:
                pcts = "—"
            print(f"  {nombre:<38} {v1s:>13} {v2s:>14} {pcts:>8}")

        fila("Longitud media de camino (min)",
             scores['lm_v1'], scores['lm_v2'], fmt="{:.2f}", unidad=" min")
        fila("Diámetro de la red (min)",
             scores['d_v1'], scores['d_v2'], fmt="{:.1f}", unidad=" min")
        flujo_pct = f"+{scores['mejora_flujo']:.0f}%"
        print(f"  {'Flujo máximo N01→N08 (p/h)':<38} {scores['f_sin']:>13} {scores['f_con']:>14} {flujo_pct:>8}")
        fila("Coeficiente de agrupamiento",
             cc_v1, cc_v2, fmt="{:.4f}", unidad="")

        nodos_v1 = len(V1_NODES)
        nodos_v2 = len(g.nodes)
        aristas_v1 = sum(1 for u in g.adj for e in g.adj[u]
                         if u in V1_NODES and e.dest in V1_NODES
                         and not e.is_setp) // 2  # aprox.
        aristas_v2 = sum(len(v) for v in g.adj.values()) // 2

        print(f"  {'Nodos en la red':<38} {nodos_v1:>13} {nodos_v2:>14} {f'+{nodos_v2-nodos_v1}':>8}")
        print(f"  {'Aristas en la red':<38} {'19 (est.)':>13} {aristas_v2:>14} {f'+{aristas_v2-19}':>8}")

        # ── Subgrafo SETP ──────────────────────────────────────────────
        print(f"\n  {'─'*66}")
        print("  Subgrafo SETP — 6 nodos Metro Sabanas")
        print(f"  {'─'*66}")
        setp_nodes, setp_adj = g.setp_subgraph()
        tipos_count = {}
        for nid, nodo in setp_nodes.items():
            cc = self.clustering_coefficient(nid, 'v2')
            vecinos_setp = len(setp_adj.get(nid, []))
            print(f"    [{nid}] {nodo.name:<32} CC={cc:.3f}  SETP-vecinos={vecinos_setp}")
            tipos_count[nodo.tipo] = tipos_count.get(nodo.tipo, 0) + 1

        # ── Agrupamiento por tipo de nodo ──────────────────────────────
        print(f"\n  {'─'*66}")
        print("  Coeficiente de Agrupamiento por Categoría (v2)")
        print(f"  {'─'*66}")
        tipos = {}
        for nid, nodo in g.nodes.items():
            cc = self.clustering_coefficient(nid, 'v2')
            tipos.setdefault(nodo.tipo, []).append(cc)
        for tipo, vals in sorted(tipos.items()):
            media = sum(vals) / len(vals)
            print(f"    {tipo:<20} n={len(vals)}  CC_medio={media:.4f}")

        # ── SETP Benefit Score ─────────────────────────────────────────
        print(f"\n  {'─'*66}")
        print("  SETP Benefit Score (índice compuesto de mejora)")
        print(f"  {'─'*66}")
        print(f"    Componente longitud media  (×0.40): {scores['mejora_lm']:>6.1f}% mejora")
        print(f"    Componente diámetro        (×0.30): {scores['mejora_diam']:>6.1f}% mejora")
        print(f"    Componente flujo máximo    (×0.30): {scores['mejora_flujo']:>6.1f}% mejora")
        print(f"    ─────────────────────────────────────────────────────")
        print(f"    SETP Benefit Score = {scores['score']:.4f}  (escala 0-1)")
        nivel = ("ALTO" if scores['score'] > 0.25 else
                 "MEDIO" if scores['score'] > 0.10 else "BAJO")
        print(f"    Nivel de impacto: {nivel}")

        # ── Validación contra valores de referencia ────────────────────
        print(f"\n  {'─'*66}")
        print("  Validación respecto a valores de referencia del enunciado")
        print(f"  {'─'*66}")
        ref = [
            ("Longitud media v1", scores['lm_v1'], 14.2, " min"),
            ("Longitud media v2", scores['lm_v2'], 10.2, " min"),
            ("Mejora longitud media", scores['mejora_lm'], 28.0, "%"),
            ("Diámetro v1", scores['d_v1'], 38.0, " min"),
            ("Diámetro v2", scores['d_v2'], 27.0, " min"),
            ("Mejora diámetro", scores['mejora_diam'], 29.0, "%"),
            ("Flujo sin SETP", scores['f_sin'], 460, " p/h"),
            ("Flujo con boost", scores['f_con'], 910, " p/h"),
            ("Mejora flujo", scores['mejora_flujo'], 98.0, "%"),
        ]
        for nombre, val_real, val_ref, unidad in ref:
            diff = abs(val_real - val_ref)
            diff_pct = (diff / val_ref * 100) if val_ref != 0 else 0
            ok = "✓" if diff_pct < 15 else "≈"
            print(f"    {ok} {nombre:<35} real={val_real:.1f}{unidad:<5} ref={val_ref}{unidad}")

        # ── Conclusión ─────────────────────────────────────────────────
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"\n  {'═'*66}")
        print("  CONCLUSIÓN")
        print(f"  {'═'*66}")
        print(f"""
  La incorporación del SETP Metro Sabanas (Estación Central + 4 PEP
  + Glorieta Sincelejito) transforma la red de movilidad de Sincelejo:

    • Longitud media : {scores['lm_v1']:.1f} → {scores['lm_v2']:.1f} min  (−{scores['mejora_lm']:.0f}%)
    • Diámetro       : {scores['d_v1']:.0f} → {scores['d_v2']:.0f} min  (−{scores['mejora_diam']:.0f}%)
    • Flujo máximo   : {scores['f_sin']} → {scores['f_con']} p/h  (+{scores['mejora_flujo']:.0f}%)
    • Nodos SETP     : 6 nodos con capacidad mínima 260 p/h

  La Estación Central (N07, 600 p/h) actúa como hub universal:
  permite cruzar toda la ciudad con un solo transbordo, demostrando
  algorítmicamente la propuesta de "un solo pasaje" del sistema SETP.

  Recomendación para la red real:
    Priorizar la habilitación de la ruta directa N07→N08 (Terminal)
    y ampliar capacidad de N01→N07 para maximizar el flujo desde
    el sector universitario hacia la Terminal de Transporte.
""")
        print(f"  Análisis ejecutado en {elapsed:.0f} ms")
        print(sep)

        return scores
