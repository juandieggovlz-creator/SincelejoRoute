# SincelejoRoute v2 — Sistema Integrado SETP Metro Sabanas

**Corporación Universitaria Antonio José de Sucre (UAJS)**  
Estructura de Datos II — 2025-I  
Proyecto Final — Semana 8

---

## 📋 Descripción

SincelejoRoute v2 modela la red de movilidad urbana de Sincelejo (Sucre, Colombia) como un **grafo ponderado dirigido** de 20 nodos y 34 aristas, integrando el Sistema Estratégico de Transporte Público (SETP) "Metro Sabanas". El sistema permite:

- Buscar nodos por nombre usando **AVL Tree** y **B-Tree**.
- Calcular rutas mínimas con y sin SETP (**Dijkstra**, **Bellman-Ford**).
- Evaluar flujo máximo de pasajeros (**Edmonds-Karp**).
- Generar la red de expansión mínima (**Prim** y **Kruskal**).
- Analizar el impacto del SETP con métricas de red, **PERT/CPM**, **Nash** y **Minimax**.
- Almacenar y consultar rutas en un **B+ Tree** con búsquedas por rango.
- Visualizar el grafo en un **dashboard web interactivo** con Leaflet.js.

---

## 📁 Estructura del Proyecto

```
SincelejoRoute/
├── data/
│   └── sincelejo_v2.csv          # Dataset del grafo (20 nodos, 34 aristas)
│
├── modulo_A/                     # Estructuras de Árbol
│   ├── trees/
│   │   ├── avl.py                # AVL Tree — búsqueda por nombre O(log n)
│   │   ├── b_tree.py             # B-Tree orden 3 — indexación por peso
│   │   └── b_plus_tree.py        # B+ Tree orden 4 — búsqueda por rango
│   ├── core/
│   │   └── router.py             # Router integrado (AVL + Dijkstra)
│   └── test_modulo_A.py          # 3 casos de prueba unitarios
│
├── modulo_B/                     # Algoritmos de Grafos + SETP
│   ├── graph/
│   │   └── graph.py              # Grafo (Node, Edge, BFS, DFS, componentes)
│   ├── algorithms/
│   │   ├── dijkstra.py           # Dijkstra con y sin descuento SETP
│   │   ├── bellman.py            # Bellman-Ford (detección de ciclos negativos)
│   │   ├── flow.py               # Edmonds-Karp (flujo máximo + corte mínimo)
│   │   ├── mst.py                # Prim MST (estándar y SETP-first)
│   │   └── kruskal.py            # Kruskal MST (con Union-Find)
│   └── test_modulo_B.py          # 3 casos de prueba unitarios
│
├── modulo_C/                     # Análisis de Impacto e Integración
│   ├── analysis/
│   │   ├── impact.py             # Análisis comparativo v1 vs v2 SETP
│   │   ├── pert.py               # Planeación PERT/CPM para obra SETP
│   │   ├── nash.py               # Equilibrio de Nash + Minimax + Alfa-Beta
│   │   ├── accessibility.py      # Métricas de accesibilidad urbana
│   │   └── tree_benchmark.py     # Benchmark AVL vs B-Tree vs B+ Tree
│   ├── visualizer/
│   │   ├── map_ui.py             # Generador de mapa HTML (Leaflet.js)
│   │   ├── map_visualizer.py     # Visualizador estático del grafo
│   │   └── server.py             # Servidor HTTP para dashboard interactivo
│   └── test_modulo_C.py          # 3 casos de prueba unitarios
│
├── main.py                       # CLI principal y servidor del dashboard
├── reporte_setp.txt              # Reporte automático de sesión
└── README.md                     # Este archivo
```

---

## 🚀 Instrucciones de Ejecución desde Cero

### Prerrequisitos

- **Python 3.10+** instalado y en el PATH del sistema.
- No se requieren librerías externas (zero-dependency).

### Instalación

```bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd SincelejoRoute

# 2. Verificar que Python está disponible
python --version
```

### Ejecución del Dashboard Interactivo (modo por defecto)

```bash
python main.py
```

Esto inicia un servidor local en `http://localhost:8000` con el dashboard web completo. Abre tu navegador en esa dirección.

### Ejecución del Modo Demo (CLI)

```bash
python main.py --demo
```

Ejecuta automáticamente las consultas estándar del docente y genera `reporte_setp.txt`.

### Ejecución de Pruebas Unitarias

```bash
python -m unittest discover
```

Ejecuta los 9 casos de prueba (3 por módulo).

---

## 🧪 Casos de Prueba

| Módulo   | Archivo                     | Tests | Descripción                                         |
|----------|-----------------------------|-------|-----------------------------------------------------|
| Módulo A | `modulo_A/test_modulo_A.py` | 3     | AVL insert/search, B-Tree insert, B+ Tree range     |
| Módulo B | `modulo_B/test_modulo_B.py` | 3     | Graph nodes, Dijkstra shortest path, Edmonds-Karp    |
| Módulo C | `modulo_C/test_modulo_C.py` | 3     | Impact analyzer, PERT planning, Nash equilibrium     |

---

## 📊 Análisis de Complejidad

### Complejidad Teórica (Big-O)

| Algoritmo / Estructura     | Operación                | Complejidad Teórica       | Justificación                                                                 |
|-----------------------------|--------------------------|---------------------------|-------------------------------------------------------------------------------|
| **AVL Tree**                | `insert()`, `search()`   | O(log n)                  | Árbol binario auto-balanceado; altura máxima = 1.44 × log₂(n).               |
| **B-Tree (t=3)**            | `insert()`, `search()`   | O(log_t n)                | Cada nodo almacena hasta 2t−1 claves; altura = O(log_t n) con t=3.           |
| **B+ Tree (m=4)**           | `search()`               | O(log_m n)                | Solo las hojas contienen datos; búsqueda desciende por nodos internos.        |
| **B+ Tree (m=4)**           | `rangeSearch()`          | O(log n + K)              | Descenso O(log n) + escaneo secuencial de K elementos en hojas enlazadas.     |
| **Dijkstra (min-heap)**     | `dijkstra()`             | O((V + E) log V)          | Cada vértice se extrae del heap O(log V); cada arista se relaja una vez.      |
| **Bellman-Ford**            | `bellman_ford()`         | O(V × E)                  | V−1 iteraciones relajando todas las E aristas.                                |
| **Edmonds-Karp (BFS)**      | `edmonds_karp()`         | O(V × E²)                 | Cada fase BFS encuentra un camino aumentante; máximo V×E fases.               |
| **Prim (min-heap)**         | `prim()`                 | O((V + E) log V)          | Similar a Dijkstra; extracción del heap por cada vértice.                     |
| **Kruskal (Union-Find)**    | `kruskal()`              | O(E log E)                | Ordenar aristas O(E log E) + Union-Find casi O(1) amortizado.                |
| **BFS / DFS**               | Recorrido completo       | O(V + E)                  | Visita cada vértice y arista exactamente una vez.                             |
| **PERT/CPM**                | Ruta crítica             | O(V + E)                  | Ordenación topológica + propagación forward/backward.                         |
| **Nash (fuerza bruta)**     | `find_nash()`            | O(S₁ × S₂)               | Examina toda la matriz de pagos para ambos jugadores.                         |
| **Minimax + Alfa-Beta**     | Poda del árbol           | O(b^d) → O(b^(d/2))      | Alfa-Beta reduce el factor de ramificación efectivo a la raíz cuadrada.       |

### Contraste Empírico (Medición Real)

Resultados obtenidos con el grafo de Sincelejo (V=20 nodos, E=34 aristas):

| Operación                        | Complejidad Teórica | Tiempo Medido | Observación                                                 |
|----------------------------------|---------------------|---------------|-------------------------------------------------------------|
| Búsqueda AVL (×1000 repeticiones)| O(log 20) ≈ 4.3 ops| < 0.10 ms     | Constante en la práctica; n=20 es tan pequeño que el overhead domina. |
| Dijkstra N01→N08                 | O(54 × log 20)      | < 0.50 ms     | Heap con 20 elementos se comporta casi como O(1) por nivel.  |
| Edmonds-Karp N01→N08             | O(20 × 34²)         | < 0.30 ms     | Solo 2-3 caminos aumentantes necesarios en este grafo.        |
| Prim MST                         | O(54 × log 20)      | < 0.20 ms     | Grafo pequeño; el heap nunca supera 20 elementos.             |
| Kruskal MST                      | O(34 × log 34)      | < 0.15 ms     | Sorting de 34 aristas es trivial + Union-Find con path compression. |
| PERT Ruta Crítica                | O(V + E) del DAG     | < 0.05 ms     | DAG de 7 tareas; prácticamente instantáneo.                   |

### Interpretación Teórica vs Empírica

1. **Todos los algoritmos ejecutan en < 1 ms** porque V=20 y E=34 son valores muy pequeños. Las constantes ocultas en Big-O (overhead de Python, acceso a memoria) dominan sobre la complejidad asintótica.

2. **El AVL Tree y el B-Tree tienen rendimiento similar** para n=20 porque ambos tienen altura ≈ 4-5 niveles. La ventaja teórica del B-Tree (menor altura por mayor ramificación) solo se manifestaría con n > 10,000.

3. **Edmonds-Karp es más rápido de lo esperado** (O(V×E²) teórico vs < 0.3 ms real) porque el grafo de Sincelejo tiene pocas rutas alternativas, requiriendo solo 2-3 iteraciones BFS en lugar del peor caso.

4. **Prim y Kruskal producen el mismo MST** (88 min estándar, 76 min con SETP), validando la corrección de ambas implementaciones. Kruskal es marginalmente más rápido por la simplicidad de Union-Find vs min-heap.

5. **La poda Alfa-Beta reduce los nodos visitados entre 40-60%** respecto a Minimax puro, confirmando la reducción teórica de O(b^d) a O(b^(d/2)).

---

## 📈 Métricas Clave del Proyecto

| Métrica                          | Sin SETP      | Con SETP       | Mejora    |
|----------------------------------|---------------|----------------|-----------|
| Longitud media de camino         | 14.5 min      | 8.5 min        | −41%      |
| Diámetro de la red               | 29 min        | 24 min         | −17%      |
| Flujo máximo N01→N08             | 460 p/h       | 910 p/h        | +98%      |
| MST (Prim)                       | 88 min        | 76 min         | −14%      |
| Nodos SETP                       | 0             | 6              | +6        |
| Componentes conexas              | 1             | 1              | =         |
| SETP Benefit Score               | —             | 0.51           | Alto      |

---

## 🗂️ Formato del CSV (`data/sincelejo_v2.csv`)

El archivo contiene dos secciones separadas por marcadores:

```
NODES
id,nombre,tipo,lat,lon,is_setp
N01,UAJS Sede C,universidad,9.296,-75.392,false
...

EDGES
origen,destino,tiempo_min,capacidad,bidireccional,is_setp
N01,N07,6,300,true,true
...
```

- **20 nodos**: 4 universidades, 3 salud, 6 SETP, 3 movilidad, 4 comercio.
- **34 aristas** (bidireccionales): peso = tiempo en minutos, capacidad en pasajeros/hora.

---

## 👥 Integrantes

| Nombre                  | Rol                           |
|-------------------------|-------------------------------|
| Juan V.                 | Desarrollo e integración      |

---

## 📝 Licencia

Proyecto académico — Corporación Universitaria UAJS, 2025.
