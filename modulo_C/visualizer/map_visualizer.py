"""
visualizer/map_visualizer.py — Módulo P18
SincelejoRoute Geo-Visualization Layer — Folium Integration

This module provides interactive HTML maps for the SincelejoRoute project.
It can draw the full graph, specific optimal routes (Dijkstra), and MSTs.
"""

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

import os
import webbrowser
from modulo_B.graph.graph import Graph

class MapVisualizer:
    """
    Handles geographical visualization of the transport network using Folium.
    """

    def __init__(self, graph: Graph):
        self.graph = graph
        self.map_file = "mapa_sincelejo.html"
        self.map = None
        
        if not HAS_FOLIUM:
            print("\n  [!] Advertencia: La librería 'folium' no está instalada.")
            print("      La visualización en mapa no estará disponible.")
            print("      Intenta: pip install folium\n")

        # Color mapping for node categories
        self.node_colors = {

            "universidad": "blue",
            "salud": "red",
            "setp": "green",
            "movilidad": "orange",
            "comercio": "gray"
        }

    def _init_map(self):
        """Initializes the map centered at the average coordinates of the nodes."""
        if not HAS_FOLIUM:
            return

        if not self.graph.nodes:
            # Default center if no nodes (Sincelejo center)
            self.map = folium.Map(location=[9.30, -75.39], zoom_start=15)
            return

        lats = [n.lat for n in self.graph.nodes.values()]
        lons = [n.lon for n in self.graph.nodes.values()]
        avg_lat = sum(lats) / len(lats)
        avg_lon = sum(lons) / len(lons)
        
        self.map = folium.Map(location=[avg_lat, avg_lon], zoom_start=15, control_scale=True)

    def draw_graph(self):
        """Draws all nodes and edges of the graph on the map."""
        if self.map is None:
            self._init_map()

        # 1. Draw Edges (Layers to distinguish SETP)
        for u_id, neighbors in self.graph.adj.items():
            u = self.graph.nodes[u_id]
            for edge in neighbors:
                v = self.graph.nodes[edge.dest]
                
                color = "green" if edge.is_setp else "gray"
                weight = 3 if edge.is_setp else 1
                opacity = 0.8 if edge.is_setp else 0.4
                
                folium.PolyLine(
                    locations=[(u.lat, u.lon), (v.lat, v.lon)],
                    color=color,
                    weight=weight,
                    opacity=opacity,
                    tooltip=f"{u.name} → {v.name} ({edge.time} min)"
                ).add_to(self.map)

        # 2. Draw Nodes
        for node in self.graph.nodes.values():
            color = self.node_colors.get(node.tipo.lower(), "black")
            icon_type = "info-sign" if node.is_setp else "tag"
            
            folium.Marker(
                location=[node.lat, node.lon],
                popup=folium.Popup(
                    f"<b>{node.name}</b><br>ID: {node.id}<br>Tipo: {node.tipo}",
                    max_width=300
                ),
                tooltip=node.name,
                icon=folium.Icon(color=color, icon=icon_type)
            ).add_to(self.map)

    def draw_route(self, path: list):
        """
        Highlights a specific path (list of node IDs) on the map.
        Typically used for Dijkstra or Bellman-Ford results.
        """
        if not path or len(path) < 2:
            return

        if self.map is None:
            self.draw_graph()

        points = []
        for nid in path:
            node = self.graph.nodes[nid]
            points.append((node.lat, node.lon))

        # Draw a thick red line for the route
        folium.PolyLine(
            locations=points,
            color="red",
            weight=8,
            opacity=0.9,
            popup="Ruta Seleccionada"
        ).add_to(self.map)

    def draw_mst(self, mst_edges: list):
        """
        Highlights the Minimum Spanning Tree edges on the map.
        Expects a list of dicts/objects with 'u' and 'v' (node IDs).
        """
        if self.map is None:
            self.draw_graph()

        for edge in mst_edges:
            # Handle different edge formats from Prim/Kruskal if necessary
            # Assuming edge is (u, v, weight) or dict with 'u','v'
            if isinstance(edge, dict):
                u_id, v_id = edge['u'], edge['v']
            else:
                u_id, v_id = edge[0], edge[1]

            u = self.graph.nodes[u_id]
            v = self.graph.nodes[v_id]
            
            folium.PolyLine(
                locations=[(u.lat, u.lon), (v.lat, v.lon)],
                color="yellow",
                weight=5,
                opacity=1.0,
                popup="Arista MST"
            ).add_to(self.map)

    def save(self):
        """Saves the map to an HTML file."""
        if self.map is None:
            self.draw_graph()
        self.map.save(self.map_file)
        print(f"  [OK] Mapa generado y guardado en: {os.path.abspath(self.map_file)}")

    def open_in_browser(self):
        """Opens the generated map in the default web browser."""
        webbrowser.open("file://" + os.path.abspath(self.map_file))
