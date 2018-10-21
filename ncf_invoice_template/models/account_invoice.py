# -*- coding: utf-8 -*-

from odoo import models, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def _get_tax_group_name(self, tax):
        tax_id = self.env['account.tax'].browse(tax)
        if tax_id.tax_group_id:
            return tax_id.tax_group_id.name
        else:
            return ""

    @api.multi
    def get_itbis_amount(self, invoice_id, price_unit, discount):
        self.ensure_one()
        currency = invoice_id and invoice_id.currency_id or None
        price = price_unit * (1 - (discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_ids.compute_all(
            price,
            currency,
            self.quantity,
            product=self.product_id,
            partner=invoice_id.partner_id)
        itbis_amount = 0
        tax_lst = taxes['taxes']
        if tax_lst:
            itbis_amount = sum([
                tax['amount'] for tax in tax_lst
                if str(self._get_tax_group_name(tax['id'])).startswith('ITBIS')
                and tax['amount'] > 0
            ])

        return itbis_amount
