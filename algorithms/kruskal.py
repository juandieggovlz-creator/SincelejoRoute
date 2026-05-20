from graph.graph import Graph


class UnionFind:
    """
    Union-Find (Disjoint Set Union) con compresion de camino y union por rango.
    Complejidad amortizada: O(alpha(n)) ~ O(1) por operacion.
    """

    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in elements}

    def find(self, x):
        """Encuentra la raiz con compresion de camino."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Compresion
        return self.parent[x]

    def union(self, x, y):
        """Une dos conjuntos por rango. Retorna True si se unieron, False si ya estaban juntos."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False  # Ya estan en el mismo conjunto (ciclo)

        # Union por rango: el arbol mas bajo se cuelga del mas alto
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1
        return True

    def connected(self, x, y):
        """Verifica si dos elementos estan en el mismo conjunto."""
        return self.find(x) == self.find(y)


class KruskalMST:
    """
    Modulo P10 - Kruskal MST con Union-Find.
    Complejidad: O(E log E + E * alpha(V)) ~ O(E log E)
    """

    def __init__(self, graph: Graph):
        self.graph = graph

    def _get_all_edges(self, setp_factor=1.0):
        """
        Genera lista de aristas unicas (sin duplicar bidireccionales).
        setp_factor: multiplicador para aristas SETP (1.0 = normal, 0.7 = prioridad SETP).
        Retorna: lista de (peso_efectivo, peso_real, u, v, is_setp)
        """
        edges = []
        seen = set()
        g = self.graph

        for u in g.adj:
            for edge in g.adj[u]:
                v = edge.dest
                # Evitar duplicados en aristas bidireccionales
                edge_key = (min(u, v), max(u, v))
                if edge_key not in seen:
                    seen.add(edge_key)
                    eff_weight = edge.time * setp_factor if edge.is_setp else edge.time
                    edges.append((eff_weight, edge.time, u, v, edge.is_setp))

        return edges

    # ─────────────────────────────────────────────────────────────────
    # Funcion 1 - Kruskal MST estandar
    # ─────────────────────────────────────────────────────────────────
    def kruskal(self):
        """
        MST estandar con Kruskal + Union-Find.
        Retorna (costo_total, mst_edges).
        """
        g = self.graph
        edges = self._get_all_edges(setp_factor=1.0)
        edges.sort(key=lambda x: x[0])  # Ordenar por peso

        uf = UnionFind(g.nodes.keys())
        mst_edges = []
        total_cost = 0.0

        for eff_w, real_w, u, v, is_setp in edges:
            if uf.union(u, v):  # Si no forma ciclo
                mst_edges.append((u, v, real_w, is_setp))
                total_cost += real_w
                if len(mst_edges) == len(g.nodes) - 1:
                    break  # MST completo

        return total_cost, mst_edges

    # ─────────────────────────────────────────────────────────────────
    # Funcion 2 - Kruskal MST con pesos SETP reducidos
    # ─────────────────────────────────────────────────────────────────
    def kruskal_setp_weighted(self):
        """
        MST con prioridad SETP (peso SETP * 0.7).
        Retorna (costo_efectivo, mst_edges).
        costo_efectivo = sum(0.7*peso si SETP, peso si no-SETP).
        """
        g = self.graph
        edges = self._get_all_edges(setp_factor=0.7)
        edges.sort(key=lambda x: x[0])

        uf = UnionFind(g.nodes.keys())
        mst_edges = []
        total_effective_cost = 0.0

        for eff_w, real_w, u, v, is_setp in edges:
            if uf.union(u, v):
                mst_edges.append((u, v, real_w, is_setp))
                total_effective_cost += eff_w
                if len(mst_edges) == len(g.nodes) - 1:
                    break

        return total_effective_cost, mst_edges

    # ─────────────────────────────────────────────────────────────────
    # Funcion 3 - Deteccion de ciclos con Union-Find
    # ─────────────────────────────────────────────────────────────────
    def cycle_detection(self, edges_list):
        """
        Detecta si un conjunto de aristas forma un ciclo.
        edges_list: lista de tuplas (u, v).
        Retorna: True si hay ciclo, False si no.
        """
        # Recopilar todos los nodos
        nodes = set()
        for u, v in edges_list:
            nodes.add(u)
            nodes.add(v)

        uf = UnionFind(nodes)
        for u, v in edges_list:
            if not uf.union(u, v):
                return True  # Ciclo detectado
        return False
