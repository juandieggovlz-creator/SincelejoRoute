import heapq
from modulo_B.graph.graph import Graph


class PrimMST:
    """
    Modulo P09 - Prim MST con prioridad SETP.
    Complejidad: O((V + E) log V) con min-heap.
    """

    def __init__(self, graph: Graph):
        self.graph = graph

    # ─────────────────────────────────────────────────────────────────
    # Funcion 1 - MST estandar (Prim)
    # Retorna: (costo_total, lista_de_aristas_mst)
    # ─────────────────────────────────────────────────────────────────
    def prim(self, start=None):
        """
        MST estandar con Prim usando pesos reales.
        Retorna (costo_total, mst_edges) donde mst_edges es lista de
        tuplas (u, v, peso_real, is_setp).
        """
        g = self.graph
        if not g.nodes:
            return 0, []

        if start is None:
            start = next(iter(g.nodes))

        visited = set()
        mst_edges = []
        total_cost = 0.0

        # (peso, nodo_destino, nodo_origen)
        pq = [(0, start, None)]

        while pq and len(visited) < len(g.nodes):
            weight, u, parent = heapq.heappop(pq)
            if u in visited:
                continue

            visited.add(u)
            if parent is not None:
                # Buscar si la arista es SETP
                is_setp = False
                for edge in g.adj.get(parent, []):
                    if edge.dest == u:
                        is_setp = edge.is_setp
                        break
                mst_edges.append((parent, u, weight, is_setp))
                total_cost += weight

            for edge in g.adj.get(u, []):
                if edge.dest not in visited:
                    heapq.heappush(pq, (edge.time, edge.dest, u))

        return total_cost, mst_edges

    # ─────────────────────────────────────────────────────────────────
    # Funcion 2 - MST con prioridad SETP (peso SETP * 0.7)
    # Retorna: (costo_efectivo, lista_de_aristas_mst)
    # El costo efectivo usa peso*0.7 para aristas SETP
    # ─────────────────────────────────────────────────────────────────
    def prim_setp_first(self, start=None):
        """
        MST que prioriza corredores Metro Sabanas.
        Aristas SETP tienen peso efectivo = peso * 0.7 durante la construccion.
        Retorna (costo_efectivo, mst_edges).
        costo_efectivo = sum(0.7*peso si SETP, peso si no-SETP).
        """
        g = self.graph
        if not g.nodes:
            return 0, []

        if start is None:
            start = next(iter(g.nodes))

        visited = set()
        mst_edges = []
        total_effective_cost = 0.0

        # (peso_efectivo, nodo_destino, nodo_origen, peso_real, is_setp)
        pq = [(0, start, None, 0, False)]

        while pq and len(visited) < len(g.nodes):
            eff_weight, u, parent, real_weight, is_setp = heapq.heappop(pq)
            if u in visited:
                continue

            visited.add(u)
            if parent is not None:
                mst_edges.append((parent, u, real_weight, is_setp))
                total_effective_cost += eff_weight

            for edge in g.adj.get(u, []):
                if edge.dest not in visited:
                    eff = edge.time * 0.7 if edge.is_setp else edge.time
                    heapq.heappush(pq, (eff, edge.dest, u, edge.time, edge.is_setp))

        return total_effective_cost, mst_edges

    # ─────────────────────────────────────────────────────────────────
    # Funcion 3 - Visualizacion ASCII del MST
    # ─────────────────────────────────────────────────────────────────
    def visualize_mst_ascii(self, mst_edges):
        """Representacion del arbol MST en consola."""
        g = self.graph
        if not mst_edges:
            print("  (MST vacio)")
            return

        # Construir arbol de adyacencia del MST
        children = {}
        all_nodes = set()
        for u, v, w, is_setp in mst_edges:
            children.setdefault(u, []).append((v, w, is_setp))
            all_nodes.add(u)
            all_nodes.add(v)

        # Encontrar raiz (nodo que no aparece como hijo)
        child_nodes = {v for _, v, _, _ in mst_edges}
        root = None
        for n in all_nodes:
            if n not in child_nodes:
                root = n
                break

        def print_tree(node, prefix="", is_last=True):
            connector = "`-- " if is_last else "|-- "
            name = g.nodes[node].name if node in g.nodes else node
            print(f"  {prefix}{connector}[{node}] {name}")

            new_prefix = prefix + ("    " if is_last else "|   ")
            kids = children.get(node, [])
            for i, (child, w, is_setp) in enumerate(kids):
                tag = " [SETP]" if is_setp else ""
                print(f"  {new_prefix}{'`' if i == len(kids)-1 else '|'}   ({w} min{tag})")
                print_tree(child, new_prefix, i == len(kids) - 1)

        if root:
            print_tree(root)

    # ─────────────────────────────────────────────────────────────────
    # Funcion 4 - Analisis de cobertura
    # ─────────────────────────────────────────────────────────────────
    def coverage_analysis(self, mst_edges):
        """Porcentaje de nodos cubiertos por el MST y estadisticas SETP."""
        g = self.graph
        total_nodes = len(g.nodes)
        nodes_in_mst = set()
        setp_edges_count = 0
        non_setp_edges_count = 0
        setp_cost = 0.0
        non_setp_cost = 0.0

        for u, v, w, is_setp in mst_edges:
            nodes_in_mst.add(u)
            nodes_in_mst.add(v)
            if is_setp:
                setp_edges_count += 1
                setp_cost += w
            else:
                non_setp_edges_count += 1
                non_setp_cost += w

        coverage = (len(nodes_in_mst) / total_nodes) * 100 if total_nodes > 0 else 0

        return {
            'total_nodes': total_nodes,
            'covered_nodes': len(nodes_in_mst),
            'coverage_pct': coverage,
            'total_edges': len(mst_edges),
            'setp_edges': setp_edges_count,
            'non_setp_edges': non_setp_edges_count,
            'setp_cost': setp_cost,
            'non_setp_cost': non_setp_cost
        }
