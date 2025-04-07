"""
trees/avl.py — Módulo P01
AVL Tree (Árbol AVL Auto-balanceado) — SincelejoRoute v2

Implementa AVLTree[str, Node] donde:
  - Clave  : nombre del nodo (String)
  - Valor  : objeto Node completo del grafo

Rotaciones implementadas: LL, RR, LR (LL+RR), RL (RR+LL)

Complejidad:
  insert()       → O(log n)
  search()       → O(log n)
  filterByType() → O(n)
  inOrderList()  → O(n)
  prettyPrint()  → O(n)

Verificación del enunciado:
  - Factor de balance ≤ 1 en todos los nodos después de 20 inserciones.
  - filterByType("setp") retorna exactamente 6 nodos.

Referencia: Cormen et al., CLRS 4ª ed., Cap. 13 (Árboles AVL).
"""

from modulo_B.graph.graph import Node


# ─────────────────────────────────────────────────────────────────────────────
# NODO INTERNO DEL AVL
# ─────────────────────────────────────────────────────────────────────────────

class AVLNode:
    """Nodo interno del árbol AVL."""

    __slots__ = ('key', 'value', 'left', 'right', 'height')

    def __init__(self, key: str, value: Node):
        self.key    = key       # nombre del nodo del grafo (clave de búsqueda)
        self.value  = value     # objeto Node completo
        self.left   = None      # hijo izquierdo
        self.right  = None      # hijo derecho
        self.height = 1         # altura del sub-árbol con raíz en este nodo


# ─────────────────────────────────────────────────────────────────────────────
# ÁRBOL AVL
# ─────────────────────────────────────────────────────────────────────────────

class AVLTree:
    """
    Árbol AVL auto-balanceado con clave String y valor Node.

    El árbol mantiene la propiedad AVL: para todo nodo,
    |altura(hijo_izq) − altura(hijo_der)| ≤ 1.

    Uso:
        avl = AVLTree()
        avl.insert("UAJS Sede C", node_obj)
        node = avl.search("UAJS Sede C")
        setp_nodes = avl.filterByType("setp")
    """

    def __init__(self):
        self._root = None
        self._size = 0

    # ──────────────────────────────────────────────────────────────────────
    # Utilidades internas de altura y factor de balance
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _height(node: AVLNode) -> int:
        """Altura del nodo (0 si es None)."""
        return node.height if node else 0

    def _update_height(self, node: AVLNode):
        """Recalcula la altura de un nodo a partir de sus hijos."""
        node.height = 1 + max(self._height(node.left),
                               self._height(node.right))

    def _balance_factor(self, node: AVLNode) -> int:
        """
        Factor de balance = altura_izq − altura_der.
        AVL exige que este valor esté en {-1, 0, +1}.
        """
        if node is None:
            return 0
        return self._height(node.left) - self._height(node.right)

    # ──────────────────────────────────────────────────────────────────────
    # Rotaciones
    # ──────────────────────────────────────────────────────────────────────

    def _rotate_right(self, y: AVLNode) -> AVLNode:
        """
        Rotación derecha (caso LL):

              y                  x
             / \\               / \\
            x   T3    →       T1   y
           / \\                   / \\
          T1  T2               T2  T3
        """
        x  = y.left
        T2 = x.right

        # Realizar rotación
        x.right = y
        y.left  = T2

        # Actualizar alturas (primero y, luego x que es la nueva raíz)
        self._update_height(y)
        self._update_height(x)

        return x   # nueva raíz del sub-árbol

    def _rotate_left(self, x: AVLNode) -> AVLNode:
        """
        Rotación izquierda (caso RR):

            x                    y
           / \\                 / \\
          T1   y     →         x  T3
              / \\             / \\
             T2  T3          T1  T2
        """
        y  = x.right
        T2 = y.left

        # Realizar rotación
        y.left  = x
        x.right = T2

        # Actualizar alturas
        self._update_height(x)
        self._update_height(y)

        return y   # nueva raíz del sub-árbol

    def _balance(self, node: AVLNode) -> AVLNode:
        """
        Rebalancea el nodo si es necesario aplicando una de las 4 rotaciones:

        LL (+2 / izq-izq) → rotación derecha simple
        RR (-2 / der-der) → rotación izquierda simple
        LR (+2 / izq-der) → rotación izquierda en hijo + derecha en raíz
        RL (-2 / der-izq) → rotación derecha en hijo + izquierda en raíz
        """
        self._update_height(node)
        bf = self._balance_factor(node)

        # ── Caso LL: el sub-árbol izquierdo es muy pesado, hijo izq también ──
        if bf > 1 and self._balance_factor(node.left) >= 0:
            return self._rotate_right(node)

        # ── Caso LR: sub-árbol izquierdo pesado, pero hijo izq tiene peso der ──
        if bf > 1 and self._balance_factor(node.left) < 0:
            node.left = self._rotate_left(node.left)   # paso 1: LL en hijo
            return self._rotate_right(node)             # paso 2: RR en raíz

        # ── Caso RR: el sub-árbol derecho es muy pesado, hijo der también ──
        if bf < -1 and self._balance_factor(node.right) <= 0:
            return self._rotate_left(node)

        # ── Caso RL: sub-árbol derecho pesado, pero hijo der tiene peso izq ──
        if bf < -1 and self._balance_factor(node.right) > 0:
            node.right = self._rotate_right(node.right)  # paso 1: RR en hijo
            return self._rotate_left(node)                # paso 2: LL en raíz

        return node  # ya estaba balanceado

    # ──────────────────────────────────────────────────────────────────────
    # Inserción
    # ──────────────────────────────────────────────────────────────────────

    def _insert(self, node: AVLNode, key: str, value: Node) -> AVLNode:
        """Inserción recursiva BST + rebalanceo AVL en el camino de retorno."""
        # Caso base: posición vacía → crear nuevo nodo
        if node is None:
            return AVLNode(key, value)

        # Comparación léxica de claves
        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            # Clave duplicada → actualizar valor
            node.value = value
            return node

        # Aplicar rebalanceo en el camino de retorno
        return self._balance(node)

    def insert(self, key: str, value: Node):
        """
        Inserta (key, value) en el AVL con balanceo automático.

        Parámetros
        ----------
        key   : str  — nombre del nodo del grafo (ej. "UAJS Sede C")
        value : Node — objeto Node completo

        Complejidad: O(log n)
        """
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"La clave debe ser un string no vacío. Recibido: {key!r}")
        self._root = self._insert(self._root, key.strip(), value)
        self._size += 1

    # ──────────────────────────────────────────────────────────────────────
    # Búsqueda
    # ──────────────────────────────────────────────────────────────────────

    def _search(self, node: AVLNode, key: str):
        """Búsqueda iterativa (más eficiente en stack que recursiva)."""
        while node:
            if key == node.key:
                return node.value
            elif key < node.key:
                node = node.left
            else:
                node = node.right
        return None

    def search(self, name: str):
        """
        Busca un nodo por nombre exacto.

        Parámetros
        ----------
        name : str — nombre del nodo (ej. "Estacion Central SETP")

        Retorna
        -------
        Node o None si no existe.

        Complejidad: O(log n)
        """
        return self._search(self._root, name.strip())

    def search_partial(self, substring: str):
        """
        Búsqueda por subcadena (case-insensitive).
        Recorre el árbol en in-order y busca coincidencias.

        Retorna lista de Node que contienen el substring en su nombre.
        Complejidad: O(n)
        """
        substring = substring.lower()
        results = []
        for node in self.in_order_list():
            if substring in node.name.lower():
                results.append(node)
        return results

    # ──────────────────────────────────────────────────────────────────────
    # Filtrado por tipo
    # ──────────────────────────────────────────────────────────────────────

    def _collect(self, node: AVLNode, predicate, result: list):
        """Recorrido in-order con predicado de filtro."""
        if node is None:
            return
        self._collect(node.left, predicate, result)
        if predicate(node.value):
            result.append(node.value)
        self._collect(node.right, predicate, result)

    def filter_by_type(self, tipo: str):
        """
        Retorna lista de Node cuyo campo `tipo` coincide con el parámetro.

        Parámetros
        ----------
        tipo : str — categoría del nodo ('setp', 'universidad', 'salud',
                     'movilidad', 'comercio')

        Retorna
        -------
        list[Node] — nodos del tipo indicado.

        Verificación: filterByType("setp") retorna exactamente 6 nodos.

        Complejidad: O(n)
        """
        result = []
        self._collect(self._root,
                      lambda n: n.tipo.lower() == tipo.lower(),
                      result)
        return result

    # Alias en inglés para compatibilidad con enunciado
    def filterByType(self, tipo: str):
        """Alias de filter_by_type() para compatibilidad con el enunciado."""
        return self.filter_by_type(tipo)

    # ──────────────────────────────────────────────────────────────────────
    # Recorridos
    # ──────────────────────────────────────────────────────────────────────

    def _in_order(self, node: AVLNode, result: list):
        if node is None:
            return
        self._in_order(node.left, result)
        result.append(node.value)
        self._in_order(node.right, result)

    def in_order_list(self):
        """
        Retorna todos los Node en orden lexicográfico ascendente (in-order).
        Complejidad: O(n)
        """
        result = []
        self._in_order(self._root, result)
        return result

    # Alias con camelCase
    def inOrderList(self):
        """Alias de in_order_list()."""
        return self.in_order_list()

    # ──────────────────────────────────────────────────────────────────────
    # Verificación de balance AVL
    # ──────────────────────────────────────────────────────────────────────

    def _verify_balance(self, node: AVLNode, violations: list):
        """Verifica recursivamente que |bf| ≤ 1 en todos los nodos."""
        if node is None:
            return
        bf = self._balance_factor(node)
        if abs(bf) > 1:
            violations.append((node.key, bf))
        self._verify_balance(node.left,  violations)
        self._verify_balance(node.right, violations)

    def is_balanced(self):
        """
        Verifica que el árbol cumple la propiedad AVL en todos los nodos.
        Retorna (True, []) si está balanceado, (False, lista_de_violaciones) si no.
        """
        violations = []
        self._verify_balance(self._root, violations)
        return (len(violations) == 0), violations

    # ──────────────────────────────────────────────────────────────────────
    # Visualización ASCII — prettyPrint
    # ──────────────────────────────────────────────────────────────────────

    def _pretty_print(self, node: AVLNode, prefix: str, is_left: bool,
                      lines: list):
        """Genera la representación visual del árbol."""
        if node is None:
            return

        connector = "├── " if is_left else "└── "
        bf = self._balance_factor(node)
        bf_str = f"  bf={bf:+d}  h={node.height}"
        setp_tag = " [SETP]" if node.value.is_setp else ""
        lines.append(f"{prefix}{connector}[{node.value.id}] {node.key}"
                     f"{setp_tag}{bf_str}")

        extension = "│   " if is_left else "    "
        self._pretty_print(node.left,  prefix + extension, True,  lines)
        self._pretty_print(node.right, prefix + extension, False, lines)

    def pretty_print(self):
        """
        Imprime el árbol AVL en consola con estructura visual,
        factor de balance y altura por nodo.
        """
        if self._root is None:
            print("  (árbol vacío)")
            return

        bf_root = self._balance_factor(self._root)
        setp_tag = " [SETP]" if self._root.value.is_setp else ""
        print(f"  └── [{self._root.value.id}] {self._root.key}"
              f"{setp_tag}  bf={bf_root:+d}  h={self._root.height}")

        lines = []
        self._pretty_print(self._root.left,  "      ", True,  lines)
        self._pretty_print(self._root.right, "      ", False, lines)
        for line in lines:
            print("  " + line)

    # Alias con camelCase
    def prettyPrint(self):
        """Alias de pretty_print()."""
        return self.pretty_print()

    # ──────────────────────────────────────────────────────────────────────
    # Propiedades y representación
    # ──────────────────────────────────────────────────────────────────────

    def __len__(self):
        return self._size

    def __repr__(self):
        balanced, _ = self.is_balanced()
        return (f"AVLTree(size={self._size}, "
                f"height={self._height(self._root)}, "
                f"balanced={'Sí' if balanced else 'No'})")
