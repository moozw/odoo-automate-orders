# Orders Auto Confirm — Odoo 18 Module

Automatically validates deliveries/receipts and posts invoices/bills when sale
or purchase orders are confirmed — controlled by company-level toggles in Settings.

---

## Features

### Sale Orders
- On confirmation, checks **on-hand stock** for all storable products
- If any item is insufficient → **blocking popup wizard** (order stays draft, no bypass)
- If stock is OK → delivery auto-validated, invoice created with **today's date** and posted

### Purchase Orders (RFQs)
- On confirmation → receipt auto-validated (all ordered quantities marked as received)
- Vendor bill created with **today's date** and posted immediately

### Settings
Both features are toggled independently per company:
- **Sales → Configuration → Settings → Order Automation**
- **Purchase → Configuration → Settings → Order Automation**

---

## Requirements

| Dependency | Purpose |
|------------|---------|
| `sale_management` | Sale order model |
| `purchase` | Purchase order model |
| `stock` | Picking / receipt validation |
| `account` | Invoice and vendor bill posting |

- Odoo **18.0** (Community or Enterprise)
- Python 3.10+

---

## Installation

1. Copy the `orders_auto_confirm` folder into your Odoo custom addons directory
2. Restart the Odoo server
3. Go to **Settings → Activate Developer Mode**
4. Go to **Apps → Update Apps List**
5. Search **Orders Auto Confirm** → **Install**

---

## Configuration

After installation:

1. Go to **Sales → Configuration → Settings**
   - Under **Order Automation**, enable **Auto-confirm delivery & invoice on sale confirmation**

2. Go to **Purchase → Configuration → Settings**
   - Under **Order Automation**, enable **Auto-confirm receipt & bill on purchase order confirmation**

3. Save settings

---

## How It Works

### Sale order flow
```
action_confirm()
  ├── company.auto_confirm_sale == False → super() only (standard Odoo)
  └── True →
        ├── _check_stock_availability()
        │     ├── all OK → proceed
        │     └── any insufficient → return blocking wizard (order stays draft)
        ├── super().action_confirm()       ← creates delivery picking
        ├── _confirm_pickings()            ← assign + validate delivery
        └── _create_and_post_invoices()    ← invoice dated today, posted
```

### Purchase order flow
```
button_confirm()
  ├── company.auto_confirm_purchase == False → super() only
  └── True →
        ├── super().button_confirm()       ← creates receipt picking
        ├── _validate_receipts()           ← set qty = demand, validate receipt
        └── _create_and_post_bills()       ← vendor bill dated today, posted
```

---

## File Structure

```
orders_auto_confirm/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_company.py          ← auto_confirm_sale + auto_confirm_purchase fields
│   ├── res_config_settings.py  ← related fields for Settings UI
│   ├── sale_order.py           ← action_confirm override
│   ├── purchase_order.py       ← button_confirm override
│   └── stock_picking.py        ← _auto_force_validate shared helper
├── wizards/
│   ├── __init__.py
│   └── stock_warning_wizard.py ← insufficient stock popup
├── views/
│   ├── res_config_settings_views.xml
│   └── stock_warning_wizard.xml
└── security/
    └── ir.model.access.csv
```

---

## Notes

- **Backorders** — receipt/delivery validation uses `skip_backorder=True`
- **Stock check** — uses `free_qty` (on-hand minus existing reservations), not forecasted quantity. Services and consumables are skipped.
- **Single-step routes only** — the module validates the first picking created for an order. Warehouses configured for multi-step routes (e.g. 2-step delivery: pick + ship, or 3-step receipt: input → quality → stock) will only have the first step auto-validated; remaining steps must be completed manually.
- **Bill creation failure** — if posting the vendor bill fails after a receipt is validated, the error is logged and the receipt remains validated. Create the bill manually from the PO; check Odoo logs for the cause.
- **Multi-company** — each company has its own toggle; the active company at confirmation time is used.
- **Single order only** — the module is designed to operate on one sales order at a time. Confirming multiple orders via list-view multi-select reverts to standard Odoo behaviour: deliveries are created in draft and invoices are not posted automatically.

---

## License

AGPL-3 — see [GNU Affero General Public License v3](https://www.gnu.org/licenses/agpl-3.0.html).
