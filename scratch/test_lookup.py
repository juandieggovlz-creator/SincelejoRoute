from modulo_B.graph.graph import Graph
from modulo_A.core.router import SincelejoRouter

def test_lookup():
    g = Graph()
    g.load_from_csv("data/sincelejo_v2.csv")
    router = SincelejoRouter(g)
    
    node1 = router.node_lookup("sede c")
    node2 = router.node_lookup("terminal")
    
    print(f"Lookup 'sede c': {node1}")
    print(f"Lookup 'terminal': {node2}")
    
    if node1 and node2:
        res = router.smart_route("sede c", "terminal")
        print(f"Route: {res}")
    else:
        print("One or both nodes not found")

if __name__ == "__main__":
    test_lookup()
