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

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        """This method is being overwritten as Odoo uses the purchase reference
            and puts it into the invoice reference (our NCF), we change this
            behaviour to use the invoice name (description)"""
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        vendor_ref = self.purchase_id.partner_ref
        if vendor_ref:
            # Here, l10n_dominicana changes self.reference to self.name
            self.name = ", ".join([self.name, vendor_ref]) if (
                self.name and vendor_ref not in self.name) else vendor_ref

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line - self.invoice_line_ids.mapped(
                'purchase_line_id'):
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.payment_term_id = self.purchase_id.payment_term_id
        self.env.context = dict(self.env.context,
                                from_purchase_order_change=True)
        self.purchase_id = False
        return {}
