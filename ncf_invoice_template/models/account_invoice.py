# © 2018 Yasmany Castillo <yasmany003@gmail.com>
# © 2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 José López <jlopez@indexa.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

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
                if str(self._get_tax_group_name(tax['id'])).startswith('ITBIS') and tax['amount'] > 0
            ])

        return itbis_amount
