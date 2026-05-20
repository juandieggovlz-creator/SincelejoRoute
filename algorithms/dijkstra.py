import heapq
from graph.graph import Graph


class DijkstraSolver:
    """
    Modulo P07 - Dijkstra con preferencia SETP.
    Complejidad: O((V + E) log V) con min-heap (heapq).
    """

    def __init__(self, graph: Graph):
        self.graph = graph
        self.last_parent = {}  # Almacena los padres del último cálculo realizado

    # ─────────────────────────────────────────────────────────────────
    # Funcion 1 — Ruta convencional (solo aristas no-SETP)
    # Modela el transporte ANTES de Metro Sabanas.
    # Retorna: (tiempo_real, lista_de_nodos)
    # ─────────────────────────────────────────────────────────────────
    def dijkstra(self, src, dst):
        """
        Dijkstra convencional: usa el tiempo base de todas las aristas.
        Representa el viaje estándar sin beneficios de carril rápido.
        """
        g = self.graph
        INF = float('inf')
        dist = {n: INF for n in g.nodes}
        parent = {n: None for n in g.nodes}
        dist[src] = 0

        pq = [(0, src)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for edge in g.adj.get(u, []):
                v = edge.dest
                new_dist = dist[u] + edge.time
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    parent[v] = u
                    heapq.heappush(pq, (new_dist, v))

        self.last_parent = parent  # Guardar estado

        if dist[dst] == INF:
            return None, []

        path = self._reconstruct_path(parent, src, dst)
        return dist[dst], path

    def setp_route(self, src, dst):
        """
        Dijkstra SETP: Incentiva el uso de corredores Metro Sabanas.
        Aplica una reducción de tiempo (eficiencia) en tramos SETP.
        """
        g = self.graph
        INF = float('inf')
        dist = {n: INF for n in g.nodes}
        parent = {n: None for n in g.nodes}
        dist[src] = 0

        pq = [(0, src)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for edge in g.adj.get(u, []):
                v = edge.dest
                # Bonus SETP: los corredores rápidos son más eficientes
                bonus = 4 if edge.is_setp else 0 
                effective_weight = max(1, edge.time - bonus)
                
                new_dist = dist[u] + effective_weight
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    parent[v] = u
                    heapq.heappush(pq, (new_dist, v))

        self.last_parent = parent  # Guardar estado

        if dist[dst] == INF:
            return None, []

        path = self._reconstruct_path(parent, src, dst)
        actual_time = self._calculate_setp_total_time(path)
        return actual_time, path

    def parent_path(self, dst):
        """
        Reconstruye el camino completo hacia dst usando los padres guardados.
        Satisface la firma pedida en P07.
        """
        if not self.last_parent:
            return []
        path = []
        curr = dst
        # Para evitar ciclos infinitos si hubiera malformación
        visited = set()
        while curr is not None and curr not in visited:
            visited.add(curr)
            path.append(curr)
            curr = self.last_parent.get(curr)
        return path[::-1]

    def all_pairs_shortest(self, sources):
        """
        Calcula la matriz de distancias mínimas entre un grupo de nodos (ej. universidades).
        Retorna diccionario {origen: {destino: costo}}.
        """
        matrix = {}
        for src in sources:
            matrix[src] = {}
            for dst in sources:
                if src == dst:
                    matrix[src][dst] = 0.0
                else:
                    t, _ = self.dijkstra(src, dst)
                    matrix[src][dst] = t if t is not None else float('inf')
        return matrix

    def _reconstruct_path(self, parent, src, dst):
        """Reconstruye el camino desde el diccionario de padres."""
        path = []
        curr = dst
        while curr is not None:
            path.append(curr)
            if curr == src:
                break
            curr = parent[curr]
        
        if not path or path[-1] != src:
            return []
        return path[::-1]

    def _calculate_setp_total_time(self, path):
        """Calcula el tiempo total aplicando los beneficios SETP en los tramos correspondientes."""
        if len(path) < 2: return 0
        g = self.graph
        total = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            for edge in g.adj.get(u, []):
                if edge.dest == v:
                    bonus = 4 if edge.is_setp else 0
                    total += max(1, edge.time - bonus)
                    break
        return total

