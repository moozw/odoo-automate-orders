* **All or nothing per company.** There is no way to automate counter sales
  while leaving project orders alone, beyond turning the setting off.
* The stock check covers storable products. Services and untracked consumables
  are not checked, since they have no tracked inventory.
* Stock is checked at confirmation. An order confirmed when stock was available
  is not re-checked later.
* Deliveries are validated in full with no backorder, so a part-shipment
  workflow is not compatible with this.
* Invoices are posted without review. Anything needing approval before posting
  should not be run through it.
* If a transfer cannot be validated automatically — because another module
  demands a wizard, for instance — that is logged and the transfer is left for a
  person.
