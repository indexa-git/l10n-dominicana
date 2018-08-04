# -*- coding: utf-8 -*-

from odoo import models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def get_itbis_amount(self, invoice_id, price_unit, discount):
        self.ensure_one()
        currency = invoice_id and invoice_id.currency_id or None
        price = price_unit * (1 - (discount or 0.0) / 100.0)
        tax = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity,
                                                    product=self.product_id, partner=self.invoice_id.partner_id)

        return tax
