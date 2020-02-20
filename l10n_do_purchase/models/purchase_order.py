# © 2018 Manuel Marquez <buzondemam@gmail.com>

from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        supplier = self.partner_id
        result['context']['default_partner_id'] = supplier.id
        del result['context']['default_reference']
        return result
