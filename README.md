# Orders Auto Confirm

Takes the clicking out of a straightforward order: confirm it and the delivery
or receipt is validated and the invoice or bill posted, in one action.

A counter sale that is paid for and taken away has no state worth tracking. The
goods leave, the invoice is raised, and making a user walk a quotation through
confirm, then reserve, then validate, then create invoice, then post is five
clicks of ceremony for a transaction that was over before it was entered.

This collapses that into confirming the order — but only when the stock is
actually there, which is the point. An order that cannot be fulfilled is
blocked rather than confirmed and left half-processed.

## What it does

### On a sale order

With the option enabled, confirming a sale order:

1. **Checks stock** for every storable product on it. Demand is summed per
   product and converted into the product's own unit of measure, so two lines
   of six for the same item are weighed against stock as twelve, and a line
   priced per dozen is weighed as twelve units.
2. **Blocks confirmation** if anything is short, showing what is missing, what
   was needed and what is available. Nothing is confirmed, delivered or
   invoiced.
3. Otherwise **confirms, validates the delivery** at full quantity with no
   backorder, and **posts the invoice**.

### On a purchase order

With the purchase option enabled, confirming a purchase order validates the
receipt and posts the vendor bill. There is no stock check — a receipt brings
goods in.

## What it changes in your database

Read this before installing on a live system. This module exists to take
several deliberate actions on one click.

* **It validates stock movements.** Deliveries and receipts are validated at
  full quantity with no backorder wizard. Stock moves and valuation are
  written.
* **It posts accounting documents.** Invoices and vendor bills are posted, which
  is final in Odoo.
* **It blocks sale order confirmation on insufficient stock.** This is a
  behaviour change for anyone used to confirming an order and sorting the stock
  out later. With the option off, nothing is blocked.
* **Both options default to off.** The module does nothing until a company
  enables it, which is the safe way to install it on a live database.
* **It adds two settings** to `res.company`, surfaced in Sales and Purchase
  settings, and a warning wizard.
* **It is per company**, not per user, per order or per warehouse.

## Configuration

| Where | Setting | Effect |
|---|---|---|
| Sales → Configuration → Settings | Auto-confirm delivery & invoice | Validate the delivery and post the invoice when a sale order is confirmed |
| Purchase → Configuration → Settings | Auto-confirm receipt & bill | Validate the receipt and post the bill when a purchase order is confirmed |

Both are off by default.

## Requirements

Odoo 18. Depends on `sale_management`, `purchase`, `stock` and `account`. No
external Python packages.

## Scope and limitations

* **All or nothing per company.** There is no way to automate counter sales
  while leaving project orders alone, beyond turning the setting off.
* The stock check covers storable products. Services and untracked consumables
  are not checked, since they have no tracked inventory.
* Stock is checked at confirmation. An order confirmed when stock was available
  is not re-checked later.
* Deliveries are validated in full with no backorder. A part-shipment workflow
  is not compatible with this.
* Invoices are posted without review. Anything needing approval before posting
  should not be run through it.
* If a transfer cannot be validated automatically — because another module
  demands a wizard, for instance — that is logged and the transfer is left for
  a person.

## Licence

AGPL-3.
