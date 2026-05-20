"""
trees/b_plus_tree.py — Módulo P03
B+ Tree orden 4 — SincelejoRoute v2

Implementa BPlusTree<Integer, Route> para almacenar y buscar rutas por su duración.
  - Orden m = 4 (máximo 3 claves por nodo interno).
  - Las hojas están enlazadas secuencialmente.
  - Métodos: insert(), rangeSearch(), fastestRoutesNo().
"""

class Route:
    """Clase que representa una ruta calculada en el grafo."""
    def __init__(self, origen: str, destino: str, path: list, costo: float, es_setp: bool):
        self.origen = origen      # ID del nodo origen (ej: "N01")
        self.destino = destino    # ID del nodo destino (ej: "N08")
        self.path = path          # Lista de IDs de nodos del camino
        self.costo = costo        # Tiempo total del trayecto en minutos
        self.es_setp = es_setp    # Booleano que indica si es ruta priorizada SETP

    def __repr__(self):
        return f"Route({self.origen} -> {self.destino}, costo={self.costo} min, SETP={self.es_setp})"


class BPlusNode:
    """Nodo interno o de hoja para el B+ Tree."""
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []          # Claves de ordenamiento (tiempo_min)
        self.children = []      # Si es hoja, lista de listas de Route. Si es interno, lista de BPlusNode.
        self.next = None        # Puntero al siguiente nodo hoja (enlace secuencial)


class BPlusTree:
    """
    Árbol B+ de orden m=4.
    Mantiene todas las claves y datos reales en las hojas enlazadas.
    """
    def __init__(self, m=4):
        self.m = m
        self.root = BPlusNode(is_leaf=True)

    def _find_leaf(self, key, node=None):
        """Desciende hasta encontrar la hoja correspondiente a la clave."""
        if node is None:
            node = self.root
        if node.is_leaf:
            return node
        
        # Buscar el hijo correcto para descender
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        return self._find_leaf(key, node.children[i])

    def search(self, key):
        """Busca una clave exacta y retorna la lista de rutas asociadas."""
        leaf = self._find_leaf(key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                return leaf.children[i]
        return None

    def insert(self, key, value):
        """Inserta una ruta en el árbol B+."""
        key = int(key)
        
        # Buscar si ya existe la clave en la hoja correspondiente
        leaf = self._find_leaf(key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                leaf.children[i].append(value)
                return

        # Si no existe, insertar nueva clave
        # La inserción empieza recursivamente desde la raíz
        promoted = self._insert(self.root, key, value)
        if promoted:
            # Si se dividió la raíz, creamos una nueva raíz con mayor altura
            promo_key, left_child, right_child = promoted
            new_root = BPlusNode(is_leaf=False)
            new_root.keys = [promo_key]
            new_root.children = [left_child, right_child]
            self.root = new_root

    def _insert(self, node, key, value):
        """Función recursiva auxiliar de inserción."""
        if node.is_leaf:
            # Insertar en la hoja en orden
            idx = 0
            while idx < len(node.keys) and key > node.keys[idx]:
                idx += 1
            node.keys.insert(idx, key)
            node.children.insert(idx, [value])
            
            # Verificar si se superó la capacidad de claves (m - 1 = 3)
            if len(node.keys) >= self.m:
                return self._split_leaf(node)
            return None
        
        # Nodo interno: buscar subárbol descendente
        idx = 0
        while idx < len(node.keys) and key >= node.keys[idx]:
            idx += 1
            
        promoted = self._insert(node.children[idx], key, value)
        if promoted:
            # Insertar la clave promovida en el nodo interno actual
            promo_key, left_child, right_child = promoted
            
            # Reemplazar el puntero del hijo por el izquierdo, y meter el derecho
            node.children[idx] = left_child
            node.keys.insert(idx, promo_key)
            node.children.insert(idx + 1, right_child)
            
            # Verificar si se superó la capacidad del nodo interno
            if len(node.keys) >= self.m:
                return self._split_internal(node)
        return None

    def _split_leaf(self, node):
        """Divide un nodo hoja."""
        mid = len(node.keys) // 2
        right = BPlusNode(is_leaf=True)
        
        right.keys = node.keys[mid:]
        right.children = node.children[mid:]
        right.next = node.next
        
        node.keys = node.keys[:mid]
        node.children = node.children[:mid]
        node.next = right
        
        # En hojas se promueve una COPIA de la clave más pequeña del nodo derecho
        return right.keys[0], node, right

    def _split_internal(self, node):
        """Divide un nodo interno."""
        mid = len(node.keys) // 2
        right = BPlusNode(is_leaf=False)
        
        # El elemento en `mid` es el que se promueve, no se queda en el hijo derecho
        promo_key = node.keys[mid]
        
        right.keys = node.keys[mid + 1:]
        right.children = node.children[mid + 1:]
        
        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]
        
        return promo_key, node, right

    def range_search(self, min_key, max_key):
        """
        Escanea secuencialmente las hojas enlazadas para buscar claves en [min_key, max_key].
        Complejidad: O(log V + K) donde K es la cantidad de elementos en el rango.
        """
        result = []
        leaf = self._find_leaf(min_key)
        
        curr = leaf
        while curr:
            for i, k in enumerate(curr.keys):
                if k > max_key:
                    return result
                if k >= min_key:
                    result.extend(curr.children[i])
            curr = curr.next
        return result

    # Alias para cumplir con la rúbrica del enunciado (camelCase)
    def rangeSearch(self, min_key, max_key):
        return self.range_search(min_key, max_key)

    def fastest_routes_no(self, n):
        """Retorna las n rutas más rápidas en el árbol."""
        result = []
        # Encontrar la primera hoja (extremo izquierdo)
        curr = self.root
        while not curr.is_leaf:
            curr = curr.children[0]
            
        # Recorrer secuencialmente agregando todas las rutas hasta tener n
        while curr:
            for routes_list in curr.children:
                for r in routes_list:
                    result.append(r)
                    if len(result) >= n:
                        return result
            curr = curr.next
        return result

    # Alias camelCase
    def fastestRoutesNo(self, n):
        return self.fastest_routes_no(n)

    def height(self):
        """Calcula la altura del árbol."""
        h = 0
        curr = self.root
        while curr:
            h += 1
            if curr.is_leaf:
                break
            curr = curr.children[0]
        return h
