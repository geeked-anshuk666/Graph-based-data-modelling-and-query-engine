-- SAP O2C dataset schema
-- 19 entity types mapped from camelCase JSONL to snake_case columns

CREATE TABLE IF NOT EXISTS sales_order_headers (
    sales_order TEXT PRIMARY KEY,
    sales_order_type TEXT,
    sales_organization TEXT,
    distribution_channel TEXT,
    organization_division TEXT,
    sales_group TEXT,
    sales_office TEXT,
    sold_to_party TEXT,
    creation_date TEXT,
    created_by_user TEXT,
    last_change_date_time TEXT,
    total_net_amount REAL,
    overall_delivery_status TEXT,
    overall_billing_status TEXT,
    overall_sd_doc_reference_status TEXT,
    transaction_currency TEXT,
    pricing_date TEXT,
    requested_delivery_date TEXT,
    header_billing_block_reason TEXT,
    delivery_block_reason TEXT,
    incoterms_classification TEXT,
    incoterms_location1 TEXT,
    customer_payment_terms TEXT,
    total_credit_check_status TEXT
);

CREATE TABLE IF NOT EXISTS sales_order_items (
    sales_order TEXT,
    sales_order_item TEXT,
    sales_order_item_category TEXT,
    material TEXT,
    requested_quantity REAL,
    requested_quantity_unit TEXT,
    transaction_currency TEXT,
    net_amount REAL,
    material_group TEXT,
    production_plant TEXT,
    storage_location TEXT,
    sales_document_rjcn_reason TEXT,
    item_billing_block_reason TEXT,
    PRIMARY KEY (sales_order, sales_order_item)
);

CREATE TABLE IF NOT EXISTS sales_order_schedule_lines (
    sales_order TEXT,
    sales_order_item TEXT,
    schedule_line TEXT,
    confirmed_delivery_date TEXT,
    order_quantity_unit TEXT,
    confd_order_qty_by_matl_avail_check REAL,
    PRIMARY KEY (sales_order, sales_order_item, schedule_line)
);

CREATE TABLE IF NOT EXISTS outbound_delivery_headers (
    delivery_document TEXT PRIMARY KEY,
    actual_goods_movement_date TEXT,
    actual_goods_movement_time TEXT,
    creation_date TEXT,
    creation_time TEXT,
    delivery_block_reason TEXT,
    hdr_general_incompletion_status TEXT,
    header_billing_block_reason TEXT,
    last_change_date TEXT,
    overall_goods_movement_status TEXT,
    overall_picking_status TEXT,
    overall_proof_of_delivery_status TEXT,
    shipping_point TEXT
);

CREATE TABLE IF NOT EXISTS outbound_delivery_items (
    delivery_document TEXT,
    delivery_document_item TEXT,
    actual_delivery_quantity REAL,
    batch TEXT,
    delivery_quantity_unit TEXT,
    item_billing_block_reason TEXT,
    last_change_date TEXT,
    plant TEXT,
    reference_sd_document TEXT,
    reference_sd_document_item TEXT,
    storage_location TEXT,
    PRIMARY KEY (delivery_document, delivery_document_item)
);

CREATE TABLE IF NOT EXISTS billing_document_headers (
    billing_document TEXT PRIMARY KEY,
    billing_document_type TEXT,
    creation_date TEXT,
    creation_time TEXT,
    last_change_date_time TEXT,
    billing_document_date TEXT,
    billing_document_is_cancelled INTEGER,
    cancelled_billing_document TEXT,
    total_net_amount REAL,
    transaction_currency TEXT,
    company_code TEXT,
    fiscal_year TEXT,
    accounting_document TEXT,
    sold_to_party TEXT
);

CREATE TABLE IF NOT EXISTS billing_document_items (
    billing_document TEXT,
    billing_document_item TEXT,
    material TEXT,
    billing_quantity REAL,
    billing_quantity_unit TEXT,
    net_amount REAL,
    transaction_currency TEXT,
    reference_sd_document TEXT,
    reference_sd_document_item TEXT,
    PRIMARY KEY (billing_document, billing_document_item)
);

CREATE TABLE IF NOT EXISTS billing_document_cancellations (
    billing_document TEXT PRIMARY KEY,
    billing_document_type TEXT,
    creation_date TEXT,
    creation_time TEXT,
    last_change_date_time TEXT,
    billing_document_date TEXT,
    billing_document_is_cancelled INTEGER,
    cancelled_billing_document TEXT,
    total_net_amount REAL,
    transaction_currency TEXT,
    company_code TEXT,
    fiscal_year TEXT,
    accounting_document TEXT,
    sold_to_party TEXT
);

CREATE TABLE IF NOT EXISTS journal_entry_items (
    company_code TEXT,
    fiscal_year TEXT,
    accounting_document TEXT,
    gl_account TEXT,
    reference_document TEXT,
    cost_center TEXT,
    profit_center TEXT,
    transaction_currency TEXT,
    amount_in_transaction_currency REAL,
    company_code_currency TEXT,
    amount_in_company_code_currency REAL,
    posting_date TEXT,
    document_date TEXT,
    accounting_document_type TEXT,
    accounting_document_item TEXT,
    assignment_reference TEXT,
    last_change_date_time TEXT,
    customer TEXT,
    financial_account_type TEXT,
    clearing_date TEXT,
    clearing_accounting_document TEXT,
    clearing_doc_fiscal_year TEXT,
    PRIMARY KEY (accounting_document, accounting_document_item)
);

CREATE TABLE IF NOT EXISTS payments (
    company_code TEXT,
    fiscal_year TEXT,
    accounting_document TEXT,
    accounting_document_item TEXT,
    clearing_date TEXT,
    clearing_accounting_document TEXT,
    clearing_doc_fiscal_year TEXT,
    amount_in_transaction_currency REAL,
    transaction_currency TEXT,
    amount_in_company_code_currency REAL,
    company_code_currency TEXT,
    customer TEXT,
    invoice_reference TEXT,
    invoice_reference_fiscal_year TEXT,
    sales_document TEXT,
    sales_document_item TEXT,
    posting_date TEXT,
    document_date TEXT,
    assignment_reference TEXT,
    gl_account TEXT,
    financial_account_type TEXT,
    profit_center TEXT,
    cost_center TEXT,
    PRIMARY KEY (accounting_document, accounting_document_item)
);

CREATE TABLE IF NOT EXISTS business_partners (
    business_partner TEXT PRIMARY KEY,
    customer TEXT,
    business_partner_category TEXT,
    business_partner_full_name TEXT,
    business_partner_grouping TEXT,
    business_partner_name TEXT,
    correspondence_language TEXT,
    created_by_user TEXT,
    creation_date TEXT,
    creation_time TEXT,
    first_name TEXT,
    form_of_address TEXT,
    industry TEXT,
    last_change_date TEXT,
    last_name TEXT,
    organization_bp_name1 TEXT,
    organization_bp_name2 TEXT,
    business_partner_is_blocked INTEGER,
    is_marked_for_archiving INTEGER
);

CREATE TABLE IF NOT EXISTS business_partner_addresses (
    business_partner TEXT,
    address_id TEXT,
    validity_start_date TEXT,
    validity_end_date TEXT,
    address_uuid TEXT,
    address_time_zone TEXT,
    city_name TEXT,
    country TEXT,
    po_box TEXT,
    po_box_deviating_city_name TEXT,
    po_box_deviating_country TEXT,
    po_box_deviating_region TEXT,
    po_box_is_without_number TEXT,
    po_box_lobby_name TEXT,
    po_box_postal_code TEXT,
    postal_code TEXT,
    region TEXT,
    street_name TEXT,
    tax_jurisdiction TEXT,
    transport_zone TEXT,
    PRIMARY KEY (business_partner, address_id)
);

CREATE TABLE IF NOT EXISTS customer_company_assignments (
    customer TEXT,
    company_code TEXT,
    accounting_clerk TEXT,
    accounting_clerk_fax_number TEXT,
    accounting_clerk_internet_address TEXT,
    accounting_clerk_phone_number TEXT,
    alternative_payer_account TEXT,
    payment_blocking_reason TEXT,
    payment_methods_list TEXT,
    payment_terms TEXT,
    reconciliation_account TEXT,
    deletion_indicator TEXT,
    customer_account_group TEXT,
    PRIMARY KEY (customer, company_code)
);

CREATE TABLE IF NOT EXISTS customer_sales_area_assignments (
    customer TEXT,
    sales_organization TEXT,
    distribution_channel TEXT,
    division TEXT,
    billing_is_blocked_for_customer TEXT,
    complete_delivery_is_defined TEXT,
    credit_control_area TEXT,
    currency TEXT,
    customer_payment_terms TEXT,
    delivery_priority TEXT,
    incoterms_classification TEXT,
    incoterms_location1 TEXT,
    sales_group TEXT,
    sales_office TEXT,
    shipping_condition TEXT,
    sls_unlmtd_ovrdeliv_is_allwd TEXT,
    supplying_plant TEXT,
    sales_district TEXT,
    exchange_rate_type TEXT,
    PRIMARY KEY (customer, sales_organization, distribution_channel, division)
);

CREATE TABLE IF NOT EXISTS products (
    product TEXT PRIMARY KEY,
    product_type TEXT,
    cross_plant_status TEXT,
    cross_plant_status_validity_date TEXT,
    creation_date TEXT,
    created_by_user TEXT,
    last_change_date TEXT,
    last_change_date_time TEXT,
    is_marked_for_deletion INTEGER,
    product_old_id TEXT,
    gross_weight REAL,
    weight_unit TEXT,
    net_weight REAL,
    product_group TEXT,
    base_unit TEXT,
    division TEXT,
    industry_sector TEXT
);

CREATE TABLE IF NOT EXISTS product_descriptions (
    product TEXT,
    language TEXT,
    product_description TEXT,
    PRIMARY KEY (product, language)
);

CREATE TABLE IF NOT EXISTS product_plants (
    product TEXT,
    plant TEXT,
    country_of_origin TEXT,
    region_of_origin TEXT,
    production_invtry_managed_loc TEXT,
    availability_check_type TEXT,
    fiscal_year_variant TEXT,
    profit_center TEXT,
    mrp_type TEXT,
    PRIMARY KEY (product, plant)
);

CREATE TABLE IF NOT EXISTS product_storage_locations (
    product TEXT,
    plant TEXT,
    storage_location TEXT,
    physical_inventory_block_ind TEXT,
    date_of_last_posted_cnt_un_rstrcd_stk TEXT,
    PRIMARY KEY (product, plant, storage_location)
);

CREATE TABLE IF NOT EXISTS plants (
    plant TEXT PRIMARY KEY,
    plant_name TEXT,
    valuation_area TEXT,
    plant_customer TEXT,
    plant_supplier TEXT,
    factory_calendar TEXT,
    default_purchasing_organization TEXT,
    sales_organization TEXT,
    address_id TEXT,
    plant_category TEXT,
    distribution_channel TEXT,
    division TEXT,
    language TEXT,
    is_marked_for_archiving INTEGER
);


-- indexes on high-join columns (referenced in architecture.md)
CREATE INDEX IF NOT EXISTS idx_soi_sales_order ON sales_order_items(sales_order);
CREATE INDEX IF NOT EXISTS idx_soi_material ON sales_order_items(material);
CREATE INDEX IF NOT EXISTS idx_soi_plant ON sales_order_items(production_plant);
CREATE INDEX IF NOT EXISTS idx_soh_sold_to ON sales_order_headers(sold_to_party);
CREATE INDEX IF NOT EXISTS idx_odi_ref_sd ON outbound_delivery_items(reference_sd_document);
CREATE INDEX IF NOT EXISTS idx_odi_delivery ON outbound_delivery_items(delivery_document);
CREATE INDEX IF NOT EXISTS idx_bdi_ref_sd ON billing_document_items(reference_sd_document);
CREATE INDEX IF NOT EXISTS idx_bdi_billing ON billing_document_items(billing_document);
CREATE INDEX IF NOT EXISTS idx_bdi_material ON billing_document_items(material);
CREATE INDEX IF NOT EXISTS idx_bdh_accounting ON billing_document_headers(accounting_document);
CREATE INDEX IF NOT EXISTS idx_bdh_sold_to ON billing_document_headers(sold_to_party);
CREATE INDEX IF NOT EXISTS idx_jei_ref_doc ON journal_entry_items(reference_document);
CREATE INDEX IF NOT EXISTS idx_jei_clearing ON journal_entry_items(clearing_accounting_document);
CREATE INDEX IF NOT EXISTS idx_jei_customer ON journal_entry_items(customer);
CREATE INDEX IF NOT EXISTS idx_pay_clearing ON payments(clearing_accounting_document);
CREATE INDEX IF NOT EXISTS idx_pay_customer ON payments(customer);
