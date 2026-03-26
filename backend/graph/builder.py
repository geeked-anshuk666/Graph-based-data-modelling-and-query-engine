"""Build the NetworkX graph from SQLite data.

Node types and edge types follow architecture.md Section "Graph Data Model".
product_storage_locations (16K rows) are deliberately excluded — too many nodes,
and they don't add meaningful value to the O2C flow visualization.
"""
import logging
import sqlite3

import networkx as nx

logger = logging.getLogger(__name__)


def build_graph(conn: sqlite3.Connection) -> nx.DiGraph:
    g = nx.DiGraph()

    # --- Sales Orders ---
    for row in conn.execute("SELECT * FROM sales_order_headers"):
        nid = f"so_{row['sales_order']}"
        g.add_node(nid, type="SalesOrder", label=f"SO {row['sales_order']}", properties=dict(row))

    # --- Sales Order Items (embedded in SO, but we link to Product) ---
    for row in conn.execute("SELECT * FROM sales_order_items"):
        so_id = f"so_{row['sales_order']}"
        prod_id = f"prod_{row['material']}" if row["material"] else None
        plant_id = f"plant_{row['production_plant']}" if row["production_plant"] else None

        if prod_id and g.has_node(so_id):
            g.add_edge(so_id, prod_id, type="CONTAINS_PRODUCT")
        if plant_id and g.has_node(so_id):
            g.add_edge(so_id, plant_id, type="PRODUCED_AT")

    # --- Deliveries ---
    for row in conn.execute("SELECT * FROM outbound_delivery_headers"):
        nid = f"del_{row['delivery_document']}"
        g.add_node(nid, type="Delivery", label=f"Del {row['delivery_document']}", properties=dict(row))

    # delivery items → link delivery back to sales order, and to plant
    for row in conn.execute("SELECT * FROM outbound_delivery_items"):
        del_id = f"del_{row['delivery_document']}"
        so_id = f"so_{row['reference_sd_document']}" if row["reference_sd_document"] else None
        plant_id = f"plant_{row['plant']}" if row["plant"] else None

        if so_id and g.has_node(del_id) and g.has_node(so_id):
            g.add_edge(del_id, so_id, type="REFERENCES_ORDER")
        if plant_id and g.has_node(del_id):
            g.add_edge(del_id, plant_id, type="SHIPPED_FROM")

    # --- Billing Documents ---
    for row in conn.execute("SELECT * FROM billing_document_headers"):
        nid = f"bill_{row['billing_document']}"
        g.add_node(nid, type="BillingDocument", label=f"Bill {row['billing_document']}", properties=dict(row))

        # link to customer
        bp_id = f"bp_{row['sold_to_party']}" if row["sold_to_party"] else None
        if bp_id:
            g.add_edge(nid, bp_id, type="BILLED_TO")

        # link to journal entry via accounting_document
        if row["accounting_document"]:
            je_id = f"je_{row['accounting_document']}"
            g.add_edge(nid, je_id, type="POSTED_TO")

    # billing items → link billing doc back to delivery
    for row in conn.execute("SELECT * FROM billing_document_items"):
        bill_id = f"bill_{row['billing_document']}"
        # reference_sd_document on billing items points to the delivery document
        del_id = f"del_{row['reference_sd_document']}" if row["reference_sd_document"] else None

        if del_id and g.has_node(bill_id) and g.has_node(del_id):
            g.add_edge(bill_id, del_id, type="REFERENCES_DELIVERY")

    # --- Customers ---
    for row in conn.execute("SELECT * FROM business_partners"):
        nid = f"bp_{row['business_partner']}"
        label = row["business_partner_full_name"] or row["business_partner_name"] or row["business_partner"]
        g.add_node(nid, type="Customer", label=f"Customer: {label}", properties=dict(row))

    # link sales orders to their customer
    for row in conn.execute("SELECT sales_order, sold_to_party FROM sales_order_headers WHERE sold_to_party IS NOT NULL"):
        so_id = f"so_{row['sales_order']}"
        bp_id = f"bp_{row['sold_to_party']}"
        if g.has_node(so_id) and g.has_node(bp_id):
            g.add_edge(so_id, bp_id, type="SOLD_TO")

    # --- Products ---
    for row in conn.execute("SELECT p.*, pd.product_description FROM products p LEFT JOIN product_descriptions pd ON p.product = pd.product AND pd.language = 'EN'"):
        nid = f"prod_{row['product']}"
        desc = row["product_description"] or row["product"]
        props = {k: row[k] for k in row.keys() if k != "product_description"}
        props["description"] = row["product_description"]
        g.add_node(nid, type="Product", label=f"Product: {desc}", properties=props)

    # --- Plants ---
    for row in conn.execute("SELECT * FROM plants"):
        nid = f"plant_{row['plant']}"
        g.add_node(nid, type="Plant", label=f"Plant: {row['plant_name'] or row['plant']}", properties=dict(row))

    # --- Journal Entries ---
    # group by accounting_document to avoid duplicate nodes from multi-line entries
    seen_je = set()
    for row in conn.execute("SELECT * FROM journal_entry_items"):
        nid = f"je_{row['accounting_document']}"
        if nid not in seen_je:
            seen_je.add(nid)
            g.add_node(nid, type="JournalEntry", label=f"JE {row['accounting_document']}", properties=dict(row))

        # link to payment via clearing_accounting_document
        if row["clearing_accounting_document"]:
            pay_id = f"pay_{row['clearing_accounting_document']}"
            g.add_edge(nid, pay_id, type="CLEARED_BY")

    # --- Payments ---
    seen_pay = set()
    for row in conn.execute("SELECT * FROM payments"):
        nid = f"pay_{row['accounting_document']}"
        if nid not in seen_pay:
            seen_pay.add(nid)
            g.add_node(nid, type="Payment", label=f"Payment {row['accounting_document']}", properties=dict(row))

    logger.info("graph built: %d nodes, %d edges", g.number_of_nodes(), g.number_of_edges())
    return g


def get_neighbors(graph: nx.DiGraph, node_id: str, depth: int = 1) -> nx.DiGraph:
    """Return the subgraph within `depth` hops of node_id."""
    if node_id not in graph:
        return nx.DiGraph()

    # collect nodes reachable within depth (both directions)
    nodes = {node_id}
    frontier = {node_id}
    for _ in range(depth):
        next_frontier = set()
        for n in frontier:
            next_frontier.update(graph.successors(n))
            next_frontier.update(graph.predecessors(n))
        nodes.update(next_frontier)
        frontier = next_frontier

    return graph.subgraph(nodes).copy()
