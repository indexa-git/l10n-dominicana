# © 2018 Manuel Marquez <buzondemam@gmail.com>

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


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('partner_id')
    def onchange_partnerid(self):

        if self.partner_id and self.type == 'in_invoice':
            if self.partner_id.purchase_journal_id:
                self.journal_id = self.partner_id.purchase_journal_id

        elif self.type == 'in_invoice' and \
                self.env.context.get('default_purchase_id'):
            purchase_order = self.env['purchase.order']
            po = purchase_order.browse(
                self.env.context.get('default_purchase_id'))
            supplier = po.partner_id
            if supplier.purchase_journal_id:
                self.journal_id = supplier.purchase_journal_id

    @api.onchange('invoice_line_ids')
    def _onchange_origin(self):
        """This method is being inherited as Odoo uses the purchase reference and
           puts it into the invoice reference (our NCF), we change this behaviour to
           use the invoice name (description)"""
        purchase_ids = self.invoice_line_ids.mapped('purchase_id')
        if purchase_ids:
            self.origin = ', '.join(purchase_ids.mapped('name'))
            self.name = ', '.join(purchase_ids.filtered('partner_ref').mapped('partner_ref')) or self.reference