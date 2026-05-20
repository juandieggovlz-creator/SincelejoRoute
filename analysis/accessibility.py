"""
analysis/accessibility.py — Módulo P04
Análisis de Accesibilidad con B+ Tree — SincelejoRoute v2

Utiliza el BPlusTree de P03 como índice para analizar los tiempos de viaje
antes y después de la implementación de Metro Sabanas.
"""

from trees.b_plus_tree import BPlusTree, Route
from algorithms.dijkstra import DijkstraSolver
from graph.graph import Graph

class AccessAnalyzer:
    """
    Analizador de accesibilidad.
    Construye dos índices B+ Tree de rutas: uno convencional y uno SETP.
    Permite calcular cobertura de red en tiempos específicos.
    """

    def __init__(self, graph: Graph):
        self.graph = graph
        self.solver = DijkstraSolver(graph)
        self.tree_conv = BPlusTree(m=4)
        self.tree_setp = BPlusTree(m=4)
        self._build_indexes()

    def _build_indexes(self):
        """Calcula todas las rutas origen-destino e inyecta en los árboles B+."""
        nodes = list(self.graph.nodes.keys())
        for u in nodes:
            for v in nodes:
                if u == v:
                    continue
                
                # 1. Ruta convencional
                t_conv, path_conv = self.solver.dijkstra(u, v)
                if t_conv is not None and t_conv < float('inf'):
                    route_c = Route(u, v, path_conv, t_conv, es_setp=False)
                    self.tree_conv.insert(int(t_conv), route_c)
                    
                # 2. Ruta SETP
                t_setp, path_setp = self.solver.setp_route(u, v)
                if t_setp is not None and t_setp < float('inf'):
                    route_s = Route(u, v, path_setp, t_setp, es_setp=True)
                    self.tree_setp.insert(int(t_setp), route_s)

    def routes_under(self, minutes, use_setp=True):
        """Retorna todas las rutas con costo menor o igual a X minutos."""
        tree = self.tree_setp if use_setp else self.tree_conv
        return tree.range_search(0, int(minutes))

    # Alias camelCase
    def routesUnder(self, minutes):
        return self.routes_under(minutes, use_setp=True)

    def university_reachability(self, node_id, minutes=20, use_setp=True):
        """
        Porcentaje de nodos del grafo total alcanzables desde una universidad
        en menos de X minutos (por defecto 20).
        """
        if node_id not in self.graph.nodes:
            return 0.0

        # Obtener todas las rutas del rango [0, minutes]
        routes = self.routes_under(minutes, use_setp)
        
        # Filtrar las que inician en node_id y contar destinos únicos
        reachable_dests = set()
        for r in routes:
            if r.origen == node_id:
                reachable_dests.add(r.destino)
                
        # Total de otros nodos posibles a alcanzar
        total_others = len(self.graph.nodes) - 1
        if total_others <= 0:
            return 0.0
            
        return (len(reachable_dests) / total_others) * 100

    # Alias camelCase
    def universityReachability(self, node_id):
        return self.university_reachability(node_id, minutes=20, use_setp=True)

    def report(self):
        """
        Genera reporte comparativo de accesibilidad.
        Demuestra la mejora pre vs post SETP.
        """
        universities = [nid for nid, n in self.graph.nodes.items() if n.tipo.lower() == 'universidad']
        
        rep = []
        rep.append("==============================================================")
        rep.append("  Reporte de Accesibilidad Universitaria — B+ Tree Indexing")
        rep.append("  Módulo P04 | SincelejoRoute v2")
        rep.append("==============================================================")
        rep.append(f"  Umbral de accesibilidad rápida: 20 minutos.\n")
        
        rep.append(f"  {'Universidad':<25} {'% Sin SETP':>12} {'% Con SETP':>12} {'Mejora':>10}")
        rep.append(f"  {'─'*25} {'─'*12} {'─'*12} {'─'*10}")
        
        for uni in universities:
            name = self.graph.nodes[uni].name
            reach_conv = self.university_reachability(uni, minutes=20, use_setp=False)
            reach_setp = self.university_reachability(uni, minutes=20, use_setp=True)
            diff = reach_setp - reach_conv
            rep.append(f"  {name:<25} {reach_conv:>11.1f}% {reach_setp:>11.1f}% {diff:>+9.1f}%")
            
        rep.append("\n  [VERIFICACIÓN] Desde N01 (UAJS Sede C):")
        n01_conv = self.university_reachability("N01", minutes=20, use_setp=False)
        n01_setp = self.university_reachability("N01", minutes=20, use_setp=True)
        rep.append(f"    - Cobertura sin SETP: {n01_conv:.1f}%")
        rep.append(f"    - Cobertura con SETP: {n01_setp:.1f}%")
        rep.append(f"    - Cumplimiento de rúbrica (~35% -> ~70%): {'Aprobado' if (30 <= n01_conv <= 40 and 65 <= n01_setp <= 75) else 'Revisar'}")
        rep.append("==============================================================")
        
        return "\n".join(rep)
