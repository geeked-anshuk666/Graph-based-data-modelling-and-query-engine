import sqlite3
from backend.graph.builder import build_graph

c = sqlite3.connect('o2c.db')
c.row_factory = sqlite3.Row
try:
    g = build_graph(c)
    print(f"Nodes: {g.number_of_nodes()}")
except Exception as e:
    print(f"Error: {e}")
