Orders Auto Confirm
===================

Takes the clicking out of a straightforward order: confirm it and the delivery
or receipt is validated and the invoice or bill posted, in one action.

A counter sale that is paid for and taken away has no state worth tracking. The
goods leave, the invoice is raised, and making a user walk a quotation through
confirm, then reserve, then validate, then create invoice, then post is five
clicks of ceremony for a transaction that was over before it was entered.

This collapses that into confirming the order — but only when the stock is
actually there, which is the point. An order that cannot be fulfilled is
blocked rather than confirmed and left half-processed.

**Sale orders.** Confirming checks stock for every storable product, summing
demand per product and converting it into the product's own unit of measure, so
two lines of six for the same item are weighed against stock as twelve and a
line priced per dozen is weighed as twelve units. If anything is short,
confirmation is blocked and the shortfall shown. Otherwise the order is
confirmed, the delivery validated in full with no backorder, and the invoice
posted.

**Purchase orders.** Confirming validates the receipt and posts the vendor bill.
There is no stock check — a receipt brings goods in.

**What it changes in your database**

This module exists to take several deliberate actions on one click.

* **It validates stock movements** at full quantity with no backorder wizard,
  writing stock moves and valuation.
* **It posts accounting documents**, which is final in Odoo.
* **It blocks sale order confirmation on insufficient stock** — a behaviour
  change for anyone used to confirming an order and sorting the stock out later.
* **Both options default to off**, so the module does nothing until a company
  enables it. That is the safe way to install it on a live database.
* It adds two settings to ``res.company`` and a warning wizard, and works per
  company rather than per user, order or warehouse.
