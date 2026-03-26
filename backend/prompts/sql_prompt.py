"""Text-to-SQL system prompt with full schema context and few-shot examples.

The schema here mirrors backend/db/schema.sql exactly. The few-shot examples
cover the 3 assignment queries plus one join pattern the LLM tends to get wrong
(billing→delivery using reference_sd_document, not billing_document).
"""

SCHEMA_CONTEXT = """
You have access to a SQLite database with the following tables:

-- Sales orders placed by customers
sales_order_headers(sales_order TEXT PK, sales_order_type, sales_organization, distribution_channel, organization_division, sales_group, sales_office, sold_to_party, creation_date, total_net_amount REAL, overall_delivery_status, overall_billing_status, transaction_currency, requested_delivery_date)

-- Line items within each sales order
sales_order_items(sales_order, sales_order_item, material, requested_quantity REAL, net_amount REAL, material_group, production_plant, storage_location)
-- sales_order_items.sales_order → sales_order_headers.sales_order
-- sales_order_items.material → products.product
-- sales_order_items.production_plant → plants.plant

-- Outbound delivery headers (shipments)
outbound_delivery_headers(delivery_document TEXT PK, creation_date, shipping_point, overall_goods_movement_status, overall_picking_status, header_billing_block_reason)

-- Delivery line items (link deliveries back to sales orders)
outbound_delivery_items(delivery_document, delivery_document_item, reference_sd_document, actual_delivery_quantity REAL, plant, storage_location)
-- outbound_delivery_items.reference_sd_document → sales_order_headers.sales_order
-- outbound_delivery_items.delivery_document → outbound_delivery_headers.delivery_document

-- Billing document headers (invoices)
billing_document_headers(billing_document TEXT PK, billing_document_type, creation_date, billing_document_date, billing_document_is_cancelled INTEGER, cancelled_billing_document, total_net_amount REAL, transaction_currency, company_code, fiscal_year, accounting_document, sold_to_party)

-- Billing line items (link billing docs back to deliveries)
billing_document_items(billing_document, billing_document_item, material, billing_quantity REAL, net_amount REAL, reference_sd_document, reference_sd_document_item)
-- billing_document_items.reference_sd_document → outbound_delivery_headers.delivery_document
-- billing_document_items.billing_document → billing_document_headers.billing_document

-- Cancelled billing documents
billing_document_cancellations(billing_document TEXT PK, cancelled_billing_document, total_net_amount REAL, sold_to_party)

-- Journal entry items (accounting postings from billing)
journal_entry_items(accounting_document, accounting_document_item, company_code, fiscal_year, gl_account, reference_document, profit_center, amount_in_transaction_currency REAL, transaction_currency, posting_date, customer, clearing_date, clearing_accounting_document)
-- journal_entry_items.reference_document links to billing_document_headers.billing_document (via accounting_document on billing side)
-- billing_document_headers.accounting_document → journal_entry_items.accounting_document

-- Customer payments
payments(accounting_document, accounting_document_item, clearing_date, clearing_accounting_document, amount_in_transaction_currency REAL, transaction_currency, customer, invoice_reference, posting_date)
-- payments linked to journal entries via clearing_accounting_document

-- Customers / business partners
business_partners(business_partner TEXT PK, customer, business_partner_full_name, business_partner_name, business_partner_is_blocked INTEGER)

-- Customer addresses
business_partner_addresses(business_partner, address_id, city_name, country, postal_code, street_name)

-- Products
products(product TEXT PK, product_type, gross_weight REAL, weight_unit, product_group, base_unit)

-- Product descriptions
product_descriptions(product, language, product_description)

-- Plants (manufacturing/warehouse locations)
plants(plant TEXT PK, plant_name, sales_organization, factory_calendar)

The O2C flow chain is:
SalesOrder → Delivery (via outbound_delivery_items.reference_sd_document = sales_order) → Billing (via billing_document_items.reference_sd_document = delivery_document) → JournalEntry (via billing_document_headers.accounting_document = journal_entry_items.accounting_document) → Payment (via journal_entry_items.clearing_accounting_document)
"""

FEW_SHOT_EXAMPLES = """
Example queries:

Q: Which products are associated with the highest number of billing documents?
SQL: SELECT i.material AS product, COUNT(DISTINCT i.billing_document) AS doc_count
FROM billing_document_items i
GROUP BY i.material
ORDER BY doc_count DESC
LIMIT 10;

Q: Trace the full flow of billing document 90504259 (Sales Order → Delivery → Billing → Journal Entry)
SQL: SELECT 'SalesOrder' AS stage, soh.sales_order AS doc_id, soh.total_net_amount AS amount, soh.creation_date
FROM billing_document_items bi
JOIN outbound_delivery_items odi ON bi.reference_sd_document = odi.delivery_document
JOIN sales_order_headers soh ON odi.reference_sd_document = soh.sales_order
WHERE bi.billing_document = '90504259'
UNION ALL
SELECT 'Delivery' AS stage, odh.delivery_document, NULL, odh.creation_date
FROM billing_document_items bi
JOIN outbound_delivery_headers odh ON bi.reference_sd_document = odh.delivery_document
WHERE bi.billing_document = '90504259'
UNION ALL
SELECT 'Billing' AS stage, bdh.billing_document, bdh.total_net_amount, bdh.creation_date
FROM billing_document_headers bdh
WHERE bdh.billing_document = '90504259'
UNION ALL
SELECT 'JournalEntry' AS stage, jei.accounting_document, jei.amount_in_transaction_currency, jei.posting_date
FROM billing_document_headers bdh
JOIN journal_entry_items jei ON bdh.accounting_document = jei.accounting_document
WHERE bdh.billing_document = '90504259';

Q: Identify sales orders that have incomplete flows — delivered but not billed
SQL: SELECT DISTINCT odi.reference_sd_document AS sales_order
FROM outbound_delivery_items odi
WHERE odi.reference_sd_document IS NOT NULL
AND odi.reference_sd_document NOT IN (
    SELECT DISTINCT bi.reference_sd_document
    FROM billing_document_items bi
    JOIN outbound_delivery_items odi2 ON bi.reference_sd_document = odi2.delivery_document
    WHERE odi2.reference_sd_document = odi.reference_sd_document
);

Q: Show me all deliveries for sales order 740506
SQL: SELECT odh.delivery_document, odh.creation_date, odh.shipping_point, odh.overall_goods_movement_status
FROM outbound_delivery_headers odh
JOIN outbound_delivery_items odi ON odh.delivery_document = odi.delivery_document
WHERE odi.reference_sd_document = '740506';
"""


def build_sql_messages(question: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are a SQL expert. Given a user question about SAP Order-to-Cash data, "
                "generate a single SQLite-compatible SELECT query. Return ONLY the SQL, nothing else. "
                "No markdown, no explanation, no code fences.\n\n"
                f"{SCHEMA_CONTEXT}\n{FEW_SHOT_EXAMPLES}"
            ),
        },
        {
            "role": "user",
            "content": f"Generate SQL for: {question}",
        },
    ]
