import logging

from fastapi import APIRouter, HTTPException, Request

from db.connection import get_db
from graph.builder import get_neighbors
from graph.serializer import to_frontend
from middleware.rate_limit import limiter
from models.schemas import NODE_ID_PATTERN

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("")
@limiter.limit("30/minute")
async def get_graph(request: Request):
    """Return the full graph as {nodes, links} for the frontend.

    The graph is built once at startup and stored in app.state.graph.
    This just serializes it — no DB hit on every call.
    """
    graph = request.app.state.graph
    data = to_frontend(graph)
    logger.info("serving graph with %d nodes and %d links", len(data['nodes']), len(data['links']))
    return data


@router.get("/node/{node_id}")
@limiter.limit("60/minute")
async def get_node(node_id: str, request: Request):
    """Return one node's properties + immediate neighbors."""
    if not NODE_ID_PATTERN.match(node_id):
        raise HTTPException(400, "invalid node id")

    graph = request.app.state.graph
    if node_id not in graph:
        raise HTTPException(404, "node not found")

    # get the node plus its 1-hop neighborhood
    subgraph = get_neighbors(graph, node_id, depth=1)
    data = to_frontend(subgraph)

    # also include the focused node's full properties
    node_data = graph.nodes[node_id]
    data["focus"] = {
        "id": node_id,
        "type": node_data.get("type", "Unknown"),
        "label": node_data.get("label", node_id),
        "properties": node_data.get("properties", {}),
    }
    return data
