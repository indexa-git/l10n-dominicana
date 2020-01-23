# © 2018 Manuel Marquez <buzondemam@gmail.com>

from odoo import models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        # Compute ref.
        super()._onchange_purchase_auto_complete()
        refs = set(self.line_ids.mapped('purchase_line_id.order_id.partner_ref'))
        refs = [ref for ref in refs if ref]
        self.narration = ','.join(refs)
        self.ref = False
