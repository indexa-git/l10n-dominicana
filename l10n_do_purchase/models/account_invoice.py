# © 2018 Manuel Marquez <buzondemam@gmail.com>


from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        """This method is being overwritten as Odoo uses the purchase reference
            and puts it into the invoice reference (our NCF), we change this
            behaviour to use the invoice name (description)"""

        if not self.journal_id.l10n_do_fiscal_journal:
            return super(AccountInvoice, self).purchase_order_change()

        vendor_ref = self.purchase_id.partner_ref
        if vendor_ref:
            # Here, l10n_dominicana changes self.reference to self.name
            self.name = ", ".join([self.name, vendor_ref]) if (
                        self.name and vendor_ref not in self.name
            ) else vendor_ref
        super(AccountInvoice, self).purchase_order_change()
        self.reference = False

        return {}
