Orders Auto Confirm
===================

Automates the post-confirmation workflow for sale and purchase orders.

**Sale orders**

When *Auto-confirm delivery & invoice* is enabled in Sales settings, confirming
a single sale order will:

1. Check on-hand stock for all storable products on the order.
2. If any product has insufficient stock, block confirmation and show a popup
   listing the shortfalls — the order remains in draft.
3. If stock is sufficient, confirm the order, immediately validate all outgoing
   deliveries (skipping the backorder wizard), and create and post a customer
   invoice dated today.

Bulk confirmation (multiple orders selected) uses standard Odoo behaviour with
no automation, so draft pickings are created normally.

**Purchase orders**

When *Auto-confirm receipt & bill* is enabled in Purchase settings, confirming
a purchase order (RFQ) will:

1. Confirm the order via the standard Odoo flow (creates the incoming receipt).
2. Pre-fill done quantities on all receipt moves and validate the receipt
   immediately (no Immediate Transfer wizard).
3. Create and post a vendor bill dated today.

If bill creation fails (e.g. account configuration issue), the receipt is still
validated and an error is logged — the bill can be created manually from the PO.

**Configuration**

Enable the features per-company under:

- **Sales → Configuration → Settings → Order Automation**
- **Purchase → Configuration → Settings → Order Automation**
