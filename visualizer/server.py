import http.server
import json
import time
import urllib.parse
import webbrowser
from datetime import datetime

from algorithms.dijkstra import DijkstraSolver
from algorithms.flow import EdmondsKarp
from algorithms.mst import PrimMST
from algorithms.kruskal import KruskalMST
from analysis.impact import SETImpactAnalyzer
from analysis.pert import get_setp_phase2_planning
from analysis.nash import GameSolver, NashSolver
from analysis.accessibility import AccessAnalyzer
from analysis.tree_benchmark import TreeBenchmark

class SincelejoRouteAPIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Mute standard console request logging to keep terminal output clean
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Serve static index.html at root
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.server.html_content.encode('utf-8'))
            return

        # Serve other API calls
        if path == "/api/nodes":
            self.handle_nodes()
        elif path == "/api/search":
            self.handle_search(query)
        elif path == "/api/route":
            self.handle_route(query)
        elif path == "/api/flow":
            self.handle_flow(query)
        elif path == "/api/mst":
            self.handle_mst(query)
        elif path == "/api/impact":
            self.handle_impact()
        elif path == "/api/benchmark":
            self.handle_benchmark()
        elif path == "/api/tree_benchmark":
            self.handle_tree_benchmark()
        elif path == "/api/accessibility":
            self.handle_accessibility()
        else:
            self.send_error(404, "Not Found")

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def handle_nodes(self):
        g = self.server.graph
        nodes_list = []
        for n in g.nodes.values():
            nodes_list.append({
                "id": n.id,
                "name": n.name,
                "type": n.tipo,
                "lat": n.lat,
                "lon": n.lon,
                "is_setp": n.is_setp
            })
        self.send_json(nodes_list)

    def handle_search(self, query):
        q = query.get('q', [''])[0].strip()
        if not q:
            self.send_json({"error": "Debe proporcionar un parámetro de búsqueda 'q'."})
            return

        g = self.server.graph
        router = self.server.router
        btree = self.server.btree

        # Medir búsqueda AVL
        t0 = time.perf_counter()
        node = router.node_lookup(q)
        t_avl = (time.perf_counter() - t0) * 1000

        # La búsqueda B-Tree ahora se mide en el módulo dedicado de Benchmark (P05)
        # ya que el B-Tree está indexado por pesos enteros, no por IDs.
        t_bt = 0.0

        if not node:
            self.send_json({"error": f"Nodo '{q}' no encontrado."})
            return

        # Obtener vecinos
        neighbors = g.adj.get(node.id, [])
        connections = []
        for e in neighbors:
            connections.append({
                "dest_id": e.dest,
                "dest_name": g.nodes[e.dest].name,
                "time": e.time,
                "capacity": e.capacity,
                "is_setp": e.is_setp
            })

        self.send_json({
            "node": {
                "id": node.id,
                "name": node.name,
                "tipo": node.tipo,
                "lat": node.lat,
                "lon": node.lon,
                "is_setp": node.is_setp
            },
            "avl_time_ms": round(t_avl, 5),
            "btree_time_ms": round(t_bt, 5),
            "connections": connections
        })

    def handle_route(self, query):
        src_inp = query.get('src', [''])[0].strip()
        dst_inp = query.get('dst', [''])[0].strip()

        if not src_inp or not dst_inp:
            self.send_json({"error": "Debe especificar parámetros 'src' y 'dst'."})
            return

        router = self.server.router
        g = self.server.graph

        res = router.smart_route(src_inp, dst_inp)
        if "error" in res:
            self.send_json({"error": res["error"]})
            return

        # Serializar la respuesta
        src_node = res["src"]
        dst_node = res["dst"]
        
        # Obtener coordenadas de ruta convencional
        conv_path = res["conventional"]["path"] or []
        conv_coords = [[g.nodes[nid].lat, g.nodes[nid].lon] for nid in conv_path]

        # Obtener coordenadas de ruta SETP
        setp_path = res["setp"]["path"] or []
        setp_coords = [[g.nodes[nid].lat, g.nodes[nid].lon] for nid in setp_path]

        # Formatear tramos
        def format_route_steps(path):
            steps = []
            for i in range(len(path)):
                nid = path[i]
                node = g.nodes[nid]
                tag = ""
                if i < len(path) - 1:
                    next_id = path[i+1]
                    is_setp_segment = False
                    for edge in g.adj.get(nid, []):
                        if edge.dest == next_id and edge.is_setp:
                            is_setp_segment = True
                            break
                    tag = " ⚡ (SETP Metro Sabanas)" if is_setp_segment else " 🚶 (Vía Normal)"
                steps.append({
                    "id": nid,
                    "name": node.name,
                    "type": node.tipo,
                    "connector": tag
                })
            return steps

        response = {
            "src": {"id": src_node.id, "name": src_node.name, "tipo": src_node.tipo},
            "dst": {"id": dst_node.id, "name": dst_node.name, "tipo": dst_node.tipo},
            "conventional": {
                "time": res["conventional"]["time"],
                "path": conv_path,
                "coords": conv_coords,
                "steps": format_route_steps(conv_path)
            },
            "setp": {
                "time": res["setp"]["time"],
                "path": setp_path,
                "coords": setp_coords,
                "steps": format_route_steps(setp_path)
            },
            "time_saved": res["time_saved"],
            "passenger_capacity": res["passenger_capacity"]
        }
        self.send_json(response)

    def handle_flow(self, query):
        src_inp = query.get('src', [''])[0].strip()
        dst_inp = query.get('dst', [''])[0].strip()

        if not src_inp or not dst_inp:
            self.send_json({"error": "Debe especificar parámetros 'src' y 'dst'."})
            return

        router = self.server.router
        g = self.server.graph

        src_node = router.node_lookup(src_inp)
        dst_node = router.node_lookup(dst_inp)

        if not src_node or not dst_node:
            self.send_json({"error": f"Origen o destino no encontrados: '{src_inp}' / '{dst_inp}'."})
            return

        ek = EdmondsKarp(g)
        f_sin = ek.edmonds_karp_no_setp(src_node.id, dst_node.id)
        f_con = ek.setp_capacity_boost(src_node.id, dst_node.id)

        # Obtener cuellos de botella
        bottlenecks = ek.bottleneck_edges(src_node.id, dst_node.id, exclude_setp=True)
        # Formatear cuellos de botella e inyectar coordenadas para dibujarlos
        bottlenecks_formatted = []
        for b in bottlenecks:
            u, v = b['origen'], b['destino']
            bottlenecks_formatted.append({
                "u": u,
                "v": v,
                "name_u": b['nombre_o'],
                "name_v": b['nombre_d'],
                "capacity": b['capacidad'],
                "is_setp": b['is_setp'],
                "coords": [
                    [g.nodes[u].lat, g.nodes[u].lon],
                    [g.nodes[v].lat, g.nodes[v].lon]
                ]
            })

        # Obtener corte mínimo
        _, cut_edges = ek.min_cut(src_node.id, dst_node.id, exclude_setp=True)
        cut_edges_formatted = []
        for c in cut_edges:
            u, v = c['origen'], c['destino']
            cut_edges_formatted.append({
                "u": u,
                "v": v,
                "name_u": g.nodes[u].name,
                "name_v": g.nodes[v].name,
                "capacity": c['capacidad'],
                "is_setp": c['is_setp']
            })

        self.send_json({
            "src": {"id": src_node.id, "name": src_node.name},
            "dst": {"id": dst_node.id, "name": dst_node.name},
            "flow_without_setp": f_sin,
            "flow_with_setp": f_con,
            "increase_pct": round(((f_con - f_sin) / f_sin * 100) if f_sin > 0 else 0, 1),
            "bottlenecks": bottlenecks_formatted,
            "cut_edges": cut_edges_formatted
        })

    def handle_mst(self, query):
        g = self.server.graph
        prim = PrimMST(g)
        kruskal = KruskalMST(g)

        cost_prim_std, edges_prim_std = prim.prim()
        cost_prim_setp, edges_prim_setp = prim.prim_setp_first()
        cost_kruskal_std, _ = kruskal.kruskal()
        cost_kruskal_setp, _ = kruskal.kruskal_setp_weighted()

        cov = prim.coverage_analysis(edges_prim_std)

        # Formatear aristas con coordenadas para pintar en mapa
        def format_edges(edges):
            formatted = []
            for u, v, w, is_setp in edges:
                formatted.append({
                    "u": u,
                    "v": v,
                    "name_u": g.nodes[u].name,
                    "name_v": g.nodes[v].name,
                    "weight": w,
                    "is_setp": is_setp,
                    "coords": [
                        [g.nodes[u].lat, g.nodes[u].lon],
                        [g.nodes[v].lat, g.nodes[v].lon]
                    ]
                })
            return formatted

        self.send_json({
            "prim_std": {
                "cost": round(cost_prim_std, 2),
                "edges": format_edges(edges_prim_std)
            },
            "prim_setp": {
                "cost": round(cost_prim_setp, 2),
                "edges": format_edges(edges_prim_setp)
            },
            "kruskal_std": {
                "cost": round(cost_kruskal_std, 2)
            },
            "kruskal_setp": {
                "cost": round(cost_kruskal_setp, 2)
            },
            "coverage": {
                "total_nodes": cov["total_nodes"],
                "covered_nodes": cov["covered_nodes"],
                "coverage_pct": round(cov["coverage_pct"], 1),
                "total_edges": cov["total_edges"],
                "setp_edges": cov["setp_edges"],
                "non_setp_edges": cov["non_setp_edges"],
                "setp_cost": round(cov["setp_cost"], 1),
                "non_setp_cost": round(cov["non_setp_cost"], 1)
            }
        })

    def handle_impact(self):
        g = self.server.graph
        analyzer = SETImpactAnalyzer(g)

        # Obtener métricas e índice de beneficio
        scores = analyzer.setp_benefit_score()
        cc_v1 = analyzer.clustering_coefficient(version='v1')
        cc_v2 = analyzer.clustering_coefficient(version='v2')

        # CC por categoría
        tipos = {}
        for nid, nodo in g.nodes.items():
            cc = analyzer.clustering_coefficient(nid, 'v2')
            tipos.setdefault(nodo.tipo, []).append(cc)
        categories_cc = {}
        for tipo, vals in tipos.items():
            categories_cc[tipo] = round(sum(vals) / len(vals), 4) if vals else 0.0

        # Subgrafo SETP
        setp_nodes, setp_adj = g.setp_subgraph()
        setp_subgraph_nodes = []
        for nid, nodo in setp_nodes.items():
            setp_subgraph_nodes.append({
                "id": nid,
                "name": nodo.name,
                "tipo": nodo.tipo,
                "cc": round(analyzer.clustering_coefficient(nid, 'v2'), 4),
                "neighbors_count": len(setp_adj.get(nid, []))
            })

        # Planeación PERT/CPM
        total_dias, ruta_critica, tareas = get_setp_phase2_planning()
        tasks_list = []
        for t in tareas.values():
            tasks_list.append({
                "name": t.name,
                "duration": t.duration,
                "predecessors": t.predecessors,
                "es": t.es,
                "ef": t.ef,
                "ls": t.ls,
                "lf": t.lf,
                "slack": t.slack,
                "is_critical": t.slack == 0
            })
        # Ordenar tareas por Early Start para que parezca una secuencia lógica
        tasks_list.sort(key=lambda x: (x["es"], x["duration"]))

        # Teoría de Juegos - Nash
        ns = NashSolver()
        nash = ns.find_nash()
        payoffs = ns.cost_matrix
        payoffs_matrix = []
        for (c, s), (p_c, p_s) in payoffs.items():
            payoffs_matrix.append({
                "conv_strategy": c,
                "setp_strategy": s,
                "payoff_conv": p_c,
                "payoff_setp": p_s,
                "is_equilibrium": (c, s) in nash
            })

        # Minimax
        gs = GameSolver()
        minimax_res = gs.run_comparison()

        self.send_json({
            "metrics": {
                "lm_v1": round(scores["lm_v1"], 2),
                "lm_v2": round(scores["lm_v2"], 2),
                "lm_improvement_pct": round(scores["mejora_lm"], 1),
                "d_v1": round(scores["d_v1"], 1),
                "d_v2": round(scores["d_v2"], 1),
                "d_improvement_pct": round(scores["mejora_diam"], 1),
                "f_sin": scores["f_sin"],
                "f_con": scores["f_con"],
                "f_improvement_pct": round(scores["mejora_flujo"], 1),
                "cc_v1": round(cc_v1, 4),
                "cc_v2": round(cc_v2, 4),
                "cc_improvement_pct": round(((cc_v2 - cc_v1) / cc_v1 * 100) if cc_v1 > 0 else 0, 1),
                "benefit_score": round(scores["score"], 4),
                "impact_level": "ALTO" if scores["score"] > 0.25 else "MEDIO" if scores["score"] > 0.10 else "BAJO"
            },
            "categories_cc": categories_cc,
            "setp_subgraph": setp_subgraph_nodes,
            "pert": {
                "total_days": total_dias,
                "critical_path": ruta_critica,
                "tasks": tasks_list
            },
            "nash": {
                "equilibrium": [list(e) for e in nash],
                "payoffs_matrix": payoffs_matrix
            },
            "minimax": minimax_res
        })

    def handle_benchmark(self):
        g = self.server.graph
        router = self.server.router

        solver = DijkstraSolver(g)
        ek = EdmondsKarp(g)
        prim = PrimMST(g)
        kruskal = KruskalMST(g)

        pruebas = [
            ("Búsqueda AVL (1,000 lookup CECAR)",   lambda: [router.avl.search('CECAR') for _ in range(1000)]),
            ("Dijkstra Optimizado (Rutas)",        lambda: solver.setp_route('N01', 'N08')),
            ("Edmonds-Karp (Capacidad de Flujo)",  lambda: ek.setp_capacity_boost('N01', 'N08')),
            ("Prim MST (Planificación Red)",       lambda: prim.prim_setp_first()),
            ("Kruskal MST (Infraestructura)",      lambda: kruskal.kruskal_setp_weighted()),
            ("Análisis PERT (Ruta de Tiempos)",    lambda: get_setp_phase2_planning()),
        ]

        results = []
        total_ms = 0
        for nombre, fn in pruebas:
            t0 = time.perf_counter()
            _ = fn()
            ms = (time.perf_counter() - t0) * 1000
            total_ms += ms
            results.append({
                "name": nombre,
                "time_ms": round(ms, 3),
                "status": "✅ Óptimo" if ms < 50 else "⚠️ Lento"
            })

        self.send_json({
            "tests": results,
            "average_ms": round(total_ms / len(pruebas), 3),
            "nodes_count": len(g.nodes),
            "edges_count": sum(len(v) for v in g.adj.values()) // 2
        })

    def handle_tree_benchmark(self):
        # Ejecuta el benchmark comparativo entre AVL, B-Tree y B+ Tree
        results = TreeBenchmark.run_benchmark()
        report = TreeBenchmark.get_report_text(results)
        self.send_json({
            "results": results,
            "report_text": report
        })

    def handle_accessibility(self):
        # Análisis de Accesibilidad de Universidades (P04)
        g = self.server.graph
        aa = AccessAnalyzer(g)
        report = aa.report()
        
        universities = [nid for nid, n in g.nodes.items() if n.tipo.lower() == 'universidad']
        data = []
        for uni in universities:
            name = g.nodes[uni].name
            reach_conv = aa.university_reachability(uni, minutes=20, use_setp=False)
            reach_setp = aa.university_reachability(uni, minutes=20, use_setp=True)
            data.append({
                "id": uni,
                "name": name,
                "reach_conv": round(reach_conv, 1),
                "reach_setp": round(reach_setp, 1),
                "improvement": round(reach_setp - reach_conv, 1)
            })
            
        self.send_json({
            "data": data,
            "report_text": report
        })


class SincelejoRouteWebServer(http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, graph, router, btree):
        super().__init__(server_address, RequestHandlerClass)
        self.graph = graph
        self.router = router
        self.btree = btree
        self.html_content = ""


def start_server(graph, router, btree, port=8000):
    server_address = ('', port)
    
    # Generate HTML once to cache in server instance
    from visualizer.map_ui import SincelejoMapUI
    ui = SincelejoMapUI(graph)
    html_content = ui.generate_html()

    httpd = SincelejoRouteWebServer(server_address, SincelejoRouteAPIHandler, graph, router, btree)
    httpd.html_content = html_content

    url = f"http://localhost:{port}"
    print(f"\n🚀 Servidor local activo en: {url}")
    print(f"💻 Abriendo SincelejoRoute Dashboard en el navegador...")
    webbrowser.open(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Apagando el servidor local...")
        httpd.server_close()
