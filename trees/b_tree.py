"""
trees/b_tree.py — Módulo P02
B-Tree orden 3 — SincelejoRoute v2

Implementa un B-Tree (t=3) donde:
  - Clave  : tiempo_min (Entero)
  - Valor  : lista de objetos (aristas/rutas) que tienen ese tiempo

Complejidad:
  insert() → O(log_t n)
  search() → O(log_t n)

Verificación del enunciado (P02):
  - Demostrar el split con los 34 pesos del grafo.
  - Comparar altura resultante del B-Tree vs AVL con los mismos valores.
"""

class BTreeNode:
    def __init__(self, t, leaf=False):
        self.t = t  # Grado mínimo (t=3)
        self.leaf = leaf
        self.keys = []      # Lista de claves (tiempo_min)
        self.values = []    # Lista de listas de valores
        self.child = []     # Hijos del nodo

class BTree:
    def __init__(self, t=3):
        self.root = BTreeNode(t, True)
        self.t = t
        self.split_count = 0  # Registra los splits para verificación

    def search(self, k, x=None):
        """Busca una clave k en el subárbol con raíz x."""
        if x is None:
            x = self.root
        
        i = 0
        while i < len(x.keys) and k > x.keys[i]:
            i += 1
        
        if i < len(x.keys) and k == x.keys[i]:
            return x.values[i]
        
        if x.leaf:
            return None
        
        return self.search(k, x.child[i])

    def insert(self, k, v):
        """Inserta un valor v asociado a la clave k (tiempo_min)."""
        # Convertir clave a entero
        k = int(k)
        
        # Primero buscar si la clave ya existe
        existing = self.search(k)
        if existing is not None:
            existing.append(v)
            return

        # Si no existe, insertar nueva clave con valor [v]
        root = self.root
        if len(root.keys) == (2 * self.t) - 1:
            # Si la raíz está llena, el árbol crece en altura
            temp = BTreeNode(self.t, False)
            self.root = temp
            temp.child.insert(0, root)
            self.split_child(temp, 0)
            self.insert_non_full(temp, k, [v])
        else:
            self.insert_non_full(root, k, [v])

    def split_child(self, x, i):
        """Divide el hijo lleno x.child[i] de un nodo x."""
        t = self.t
        y = x.child[i]
        z = BTreeNode(t, y.leaf)
        x.child.insert(i + 1, z)
        x.keys.insert(i, y.keys[t - 1])
        x.values.insert(i, y.values[t - 1])
        
        z.keys = y.keys[t: (2 * t) - 1]
        z.values = y.values[t: (2 * t) - 1]
        y.keys = y.keys[0: t - 1]
        y.values = y.values[0: t - 1]
        
        if not y.leaf:
            z.child = y.child[t: 2 * t]
            y.child = y.child[0: t]
            
        self.split_count += 1

    def insert_non_full(self, x, k, v):
        """Inserta la clave k en un nodo x que no está lleno."""
        i = len(x.keys) - 1
        if x.leaf:
            x.keys.append(None)
            x.values.append(None)
            while i >= 0 and k < x.keys[i]:
                x.keys[i + 1] = x.keys[i]
                x.values[i + 1] = x.values[i]
                i -= 1
            x.keys[i + 1] = k
            x.values[i + 1] = v
        else:
            while i >= 0 and k < x.keys[i]:
                i -= 1
            i += 1
            if len(x.child[i].keys) == (2 * self.t) - 1:
                self.split_child(x, i)
                if k > x.keys[i]:
                    i += 1
            self.insert_non_full(x.child[i], k, v)

    def height(self, node=None):
        """Calcula la altura del B-Tree."""
        if node is None:
            node = self.root
        h = 0
        curr = node
        while curr:
            h += 1
            if curr.leaf:
                break
            curr = curr.child[0] if curr.child else None
        return h

    def traverse(self, x=None):
        """Recorrido in-order que retorna lista de (clave, valores)."""
        if x is None:
            x = self.root
        res = []
        def _traverse(node):
            for i in range(len(node.keys)):
                if not node.leaf:
                    _traverse(node.child[i])
                res.append((node.keys[i], node.values[i]))
            if not node.leaf:
                _traverse(node.child[len(node.keys)])
        _traverse(x)
        return res
