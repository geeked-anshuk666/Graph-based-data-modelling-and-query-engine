"""Convert NetworkX DiGraph to the {nodes, links} JSON format
that react-force-graph-2d expects."""
import networkx as nx


def to_frontend(graph: nx.DiGraph) -> dict:
    nodes = []
    for nid, data in graph.nodes(data=True):
        nodes.append({
            "id": nid,
            "type": data.get("type", "Unknown"),
            "label": data.get("label", nid),
            "properties": data.get("properties", {}),
        })

    links = []
    for src, tgt, data in graph.edges(data=True):
        links.append({
            "source": src,
            "target": tgt,
            "type": data.get("type", "RELATED"),
        })

    return {"nodes": nodes, "links": links}
