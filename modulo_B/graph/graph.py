import csv

class Node:
    def __init__(self, id, name, tipo, lat, lon, is_setp):
        self.id = id
        self.name = name
        self.tipo = tipo
        self.lat = float(lat)
        self.lon = float(lon)
        self.is_setp = str(is_setp).strip().lower() == 'true'

    def __repr__(self):
        return f"Node({self.id}, {self.name})"

class Edge:
    def __init__(self, dest, time, capacity, is_setp):
        self.dest = dest
        self.time = float(time)
        self.capacity = int(capacity)
        self.is_setp = str(is_setp).strip().lower() == 'true'

    def __repr__(self):
        return f"Edge({self.dest}, time={self.time}, cap={self.capacity})"

class Graph:
    def __init__(self):
        self.nodes = {}  # id -> Node
        self.adj = {}    # id -> list of Edge (Lista de adyacencia)

    def add_node(self, node):
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            self.adj[node.id] = []

    def add_edge(self, u, v, weight, capacity, is_setp, bidirectional=True):
        if u not in self.nodes or v not in self.nodes:
            print(f"Advertencia: Nodo desconocido en la arista {u}-{v}. Se ignorará.")
            return

        self.adj[u].append(Edge(v, weight, capacity, is_setp))
        if bidirectional:
            self.adj[v].append(Edge(u, weight, capacity, is_setp))

    def load_from_csv(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        mode = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line == 'NODES':
                mode = 'NODES'
                continue
            elif line == 'EDGES':
                mode = 'EDGES'
                continue
                
            # Saltar cabeceras
            if line.startswith('id,nombre') or line.startswith('origen,destino'):
                continue
                
            parts = line.split(',')
            
            if mode == 'NODES' and len(parts) == 6:
                node_id, name, tipo, lat, lon, is_setp = parts
                node = Node(node_id, name, tipo, lat, lon, is_setp)
                self.add_node(node)
                
            elif mode == 'EDGES' and len(parts) == 6:
                u, v, weight, capacity, bidirectional, is_setp = parts
                bidir = bidirectional.strip().lower() == 'true'
                self.add_edge(u, v, weight, capacity, is_setp, bidirectional=bidir)

    def bfs(self, start_id):
        """Retorna un diccionario con los nodos visitados y su nivel desde el origen."""
        if start_id not in self.nodes:
            return {}
            
        visited = {start_id: 0} # {node_id: nivel}
        queue = [start_id]
        
        while queue:
            current = queue.pop(0)
            current_level = visited[current]
            
            for edge in self.adj[current]:
                if edge.dest not in visited:
                    visited[edge.dest] = current_level + 1
                    queue.append(edge.dest)
                    
        return visited

    def dfs(self, start_id):
        """Retorna timestamps de descubrimiento y finalización (desc_time, finish_time)"""
        visited = set()
        discovery_time = {}
        finish_time = {}
        time = [0] # Usamos una lista para pasar por referencia a la funcion anidada
        
        def dfs_visit(u):
            time[0] += 1
            discovery_time[u] = time[0]
            visited.add(u)
            
            for edge in self.adj.get(u, []):
                if edge.dest not in visited:
                    dfs_visit(edge.dest)
                    
            time[0] += 1
            finish_time[u] = time[0]

        if start_id in self.nodes:
            dfs_visit(start_id)

        return discovery_time, finish_time

    def setp_subgraph(self):
        """
        Extrae el subgrafo formado solo por nodos y aristas SETP.
        Retorna: (dict nodos SETP, dict adj SETP)
        P06 — Resultado esperado: 6 nodos SETP.
        """
        setp_nodes = {nid: n for nid, n in self.nodes.items() if n.is_setp}
        setp_adj = {}
        for nid in setp_nodes:
            setp_adj[nid] = [e for e in self.adj.get(nid, [])
                             if e.is_setp and e.dest in setp_nodes]
        return setp_nodes, setp_adj

    def connected_components(self):
        """
        Identifica componentes conexas del grafo mediante BFS.
        Retorna: lista de conjuntos, cada uno es una componente conexa.
        Util para verificar qué componentes quedan si se elimina un nodo (ej. N07).
        """
        visited = set()
        components = []
        for start in self.nodes:
            if start not in visited:
                component = set()
                queue = [start]
                visited.add(start)
                while queue:
                    current = queue.pop(0)
                    component.add(current)
                    for edge in self.adj.get(current, []):
                        if edge.dest not in visited:
                            visited.add(edge.dest)
                            queue.append(edge.dest)
                components.append(component)
        return components

    def has_cycle(self):
        """
        Detecta ciclos usando coloracion DFS: blanco(0)/gris(1)/negro(2).
        Retorna True si hay ciclo, False si el grafo es aciclico (DAG).
        Complejidad: O(V + E).
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in self.nodes}
        cycle_found = [False]

        def dfs_color(u):
            if cycle_found[0]:
                return
            color[u] = GRAY
            for edge in self.adj.get(u, []):
                v = edge.dest
                if color[v] == GRAY:
                    cycle_found[0] = True
                    return
                if color[v] == WHITE:
                    dfs_color(v)
            color[u] = BLACK

        for node in self.nodes:
            if color[node] == WHITE:
                dfs_color(node)

        return cycle_found[0]
