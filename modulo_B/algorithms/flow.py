from collections import defaultdict, deque
from modulo_B.graph.graph import Graph


class FlowNetwork:
    """Red de flujo con grafo residual para Edmonds-Karp."""

    def __init__(self):
        self.graph = defaultdict(dict)

    def add_edge(self, u, v, capacity):
        self.graph[u][v] = self.graph[u].get(v, 0) + capacity
        if v not in self.graph or u not in self.graph[v]:
            self.graph[v][u] = self.graph[v].get(u, 0)

    def get_nodes(self):
        return set(self.graph.keys())


class EdmondsKarp:
    """
    Modulo P11 - Flujo maximo Edmonds-Karp.
    Complejidad: O(V * E^2)
    """

    def __init__(self, graph: Graph):
        self.source_graph = graph

    def _build_flow_network(self, boost_setp=False, exclude_setp=False):
        """
        Construye red de flujo desde el grafo.
        boost_setp: aristas SETP tienen capacidad * 1.5
        exclude_setp: excluir aristas SETP (simula red sin Metro Sabanas)
        """
        g = self.source_graph
        fn = FlowNetwork()

        for u in g.adj:
            for edge in g.adj[u]:
                if exclude_setp and edge.is_setp:
                    continue
                cap = edge.capacity
                if boost_setp and edge.is_setp:
                    cap = int(cap * 1.5)
                fn.add_edge(u, edge.dest, cap)

        return fn

    def _bfs(self, network, source, sink, parent):
        visited = {source}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v, cap in network[u].items():
                if v not in visited and cap > 0:
                    visited.add(v)
                    parent[v] = u
                    if v == sink:
                        return True
                    queue.append(v)
        return False

    def _run_edmonds_karp(self, source, sink, boost_setp=False, exclude_setp=False):
        fn = self._build_flow_network(boost_setp, exclude_setp)
        residual = defaultdict(dict)

        for u in fn.graph:
            for v, cap in fn.graph[u].items():
                residual[u][v] = cap
                if u not in residual[v]:
                    residual[v][u] = 0

        max_flow = 0
        while True:
            parent = {}
            if not self._bfs(residual, source, sink, parent):
                break
            path_flow = float('inf')
            v = sink
            while v != source:
                u = parent[v]
                path_flow = min(path_flow, residual[u][v])
                v = u
            v = sink
            while v != source:
                u = parent[v]
                residual[u][v] -= path_flow
                residual[v][u] = residual.get(v, {}).get(u, 0) + path_flow
                v = u
            max_flow += path_flow

        return max_flow, residual

    # ─────────────────────────────────────────────────────────────────
    # Flujo maximo estandar (todas las aristas, sin boost)
    # ─────────────────────────────────────────────────────────────────
    def edmonds_karp(self, source, sink):
        flow, _ = self._run_edmonds_karp(source, sink)
        return flow

    # ─────────────────────────────────────────────────────────────────
    # Flujo maximo SIN aristas SETP (antes de Metro Sabanas)
    # ─────────────────────────────────────────────────────────────────
    def edmonds_karp_no_setp(self, source, sink):
        flow, _ = self._run_edmonds_karp(source, sink, exclude_setp=True)
        return flow

    # ─────────────────────────────────────────────────────────────────
    # Flujo maximo CON boost SETP (+50% capacidad)
    # ─────────────────────────────────────────────────────────────────
    def setp_capacity_boost(self, source, sink):
        flow, _ = self._run_edmonds_karp(source, sink, boost_setp=True)
        return flow

    # ─────────────────────────────────────────────────────────────────
    # Corte minimo
    # ─────────────────────────────────────────────────────────────────
    def min_cut(self, source, sink, boost_setp=False, exclude_setp=False):
        _, residual = self._run_edmonds_karp(source, sink, boost_setp, exclude_setp)
        visited = {source}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v, cap in residual.get(u, {}).items():
                if v not in visited and cap > 0:
                    visited.add(v)
                    queue.append(v)

        cut_edges = []
        g = self.source_graph
        for u in visited:
            for edge in g.adj.get(u, []):
                if exclude_setp and edge.is_setp:
                    continue
                if edge.dest not in visited:
                    cap = int(edge.capacity * 1.5) if (boost_setp and edge.is_setp) else edge.capacity
                    cut_edges.append({
                        'origen': u, 'destino': edge.dest,
                        'capacidad': cap, 'is_setp': edge.is_setp
                    })
        return visited, cut_edges

    # ─────────────────────────────────────────────────────────────────
    # Aristas cuello de botella (saturadas)
    # ─────────────────────────────────────────────────────────────────
    def bottleneck_edges(self, source, sink, boost_setp=False, exclude_setp=False):
        fn = self._build_flow_network(boost_setp, exclude_setp)
        _, residual = self._run_edmonds_karp(source, sink, boost_setp, exclude_setp)

        saturated = []
        g = self.source_graph
        seen = set()
        for u in g.adj:
            for edge in g.adj[u]:
                if exclude_setp and edge.is_setp:
                    continue
                v = edge.dest
                key = (min(u, v), max(u, v))
                if key in seen:
                    continue
                original_cap = fn.graph.get(u, {}).get(v, 0)
                remaining = residual.get(u, {}).get(v, 0)
                if original_cap > 0 and remaining == 0:
                    cap = int(edge.capacity * 1.5) if (boost_setp and edge.is_setp) else edge.capacity
                    seen.add(key)
                    saturated.append({
                        'origen': u, 'destino': v,
                        'capacidad': cap, 'is_setp': edge.is_setp,
                        'nombre_o': g.nodes[u].name,
                        'nombre_d': g.nodes[v].name
                    })
        return saturated

    # ─────────────────────────────────────────────────────────────────
    # Capacidad de evacuacion
    # ─────────────────────────────────────────────────────────────────
    def evacuation_capacity(self, src, dst):
        return self.setp_capacity_boost(src, dst)
