from modulo_B.graph.graph import Graph


class BellmanFordSolver:
    """
    Modulo P08 - Bellman-Ford con descuento SETP.
    Permite pesos negativos (bono de -3 min en aristas SETP).
    Complejidad: O(V * E)
    """

    def __init__(self, graph: Graph, setp_discount=3):
        self.graph = graph
        self.setp_discount = setp_discount  # Bono SETP en minutos

    def _get_all_edges(self):
        """Genera lista de todas las aristas (u, v, peso_efectivo, peso_real)."""
        edges = []
        g = self.graph
        for u in g.adj:
            for edge in g.adj[u]:
                real_weight = edge.time
                # El SETP otorga un bono que genera pesos negativos
                effective = real_weight - self.setp_discount if edge.is_setp else real_weight
                edges.append((u, edge.dest, effective, real_weight))
        return edges

    # ─────────────────────────────────────────────────────────────────
    # Funcion 1 - Bellman-Ford: distancias a todos los nodos
    # Soporta pesos negativos (bono SETP de -3 min)
    # Complejidad: O(V * E)
    # ─────────────────────────────────────────────────────────────────
    def bellman_ford(self, src):
        """
        Calcula distancias minimas desde src a todos los nodos.
        Soporta aristas con peso negativo (bono SETP).
        Retorna: (dist, parent) o None si hay ciclo negativo.
        """
        g = self.graph
        INF = float('inf')
        dist = {n: INF for n in g.nodes}
        parent = {n: None for n in g.nodes}
        dist[src] = 0

        edges = self._get_all_edges()
        V = len(g.nodes)

        # Relajar V-1 veces (propiedad fundamental de Bellman-Ford)
        for i in range(V - 1):
            updated = False
            for u, v, w, _ in edges:
                if dist[u] != INF and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    parent[v] = u
                    updated = True
            # Optimizacion: si no hubo cambios, ya convergio
            if not updated:
                break

        # Verificar ciclo negativo (iteracion V)
        for u, v, w, _ in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                return None, None  # Ciclo negativo detectado

        return dist, parent

    # ─────────────────────────────────────────────────────────────────
    # Funcion 2 - Detectar ciclo negativo
    # ─────────────────────────────────────────────────────────────────
    def has_negative_cycle(self):
        """
        Detecta si el grafo con descuento SETP genera un ciclo negativo.
        Ejecuta Bellman-Ford desde cada nodo para cobertura completa.
        """
        # Intentar desde un nodo cualquiera (grafo conexo)
        for src in self.graph.nodes:
            dist, parent = self.bellman_ford(src)
            if dist is None:
                return True
            break  # Si es conexo, basta con un origen
        return False

    # ─────────────────────────────────────────────────────────────────
    # Funcion 3 - Listar aristas con peso negativo
    # ─────────────────────────────────────────────────────────────────
    def negative_weight_edges(self):
        """Retorna lista de aristas cuyo peso efectivo es < 0."""
        result = []
        edges = self._get_all_edges()
        seen = set()
        for u, v, w_eff, w_real in edges:
            if w_eff < 0 and (u, v) not in seen:
                result.append({
                    'origen': u,
                    'destino': v,
                    'peso_real': w_real,
                    'peso_efectivo': w_eff,
                    'descuento': self.setp_discount
                })
                seen.add((u, v))
        return result

    # ─────────────────────────────────────────────────────────────────
    # Funcion 4 - Reconstruir ruta y calcular tiempo real
    # ─────────────────────────────────────────────────────────────────
    def shortest_path(self, src, dst):
        """
        Ruta minima con Bellman-Ford (soporta pesos negativos).
        Retorna: (tiempo_real, camino) o (None, []) si no hay ruta.
        """
        dist, parent = self.bellman_ford(src)
        if dist is None:
            return None, []  # Ciclo negativo
        if dist.get(dst) == float('inf'):
            return None, []

        # Reconstruir camino
        path = []
        current = dst
        while current is not None:
            path.append(current)
            current = parent[current]
        path.reverse()

        # Calcular tiempo REAL del camino
        g = self.graph
        actual_time = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            for edge in g.adj.get(u, []):
                if edge.dest == v:
                    actual_time += edge.time
                    break

        return actual_time, path
