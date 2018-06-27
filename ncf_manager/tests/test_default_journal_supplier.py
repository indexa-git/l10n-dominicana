# -*- coding: utf-8 -*-
# Copyright 2018 Iterativo - Manuel Marquez <buzondemam@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import random

from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class TestDefaultJournalSupplier(common.TransactionCase):

    def _get_purchase_order(self):
        """Confirm a purchase order and returns the order."""

        purchase_order = self.env['purchase.order']
        rfq_orders = purchase_order.search([('state', '=', 'draft')])
        if not rfq_orders:
            raise ValidationError(_('No purchase orders in state RFQ'))
        po = random.choice(rfq_orders)
        po.button_confirm()
        return po

    def _get_purchase_invoice(self, po):
        """Create an invoice for a purchase and returns the invoice."""

        account_invoice = self.env['account.invoice']
        partner = po.partner_id
        demo_user = self.env.ref('base.user_demo')
        payment_term = po.payment_term_id

        invoice_vals = {
            'partner_id': partner.id,
            'user_id': demo_user.id,
            'payment_term_id': payment_term.id,
            'type': 'in_invoice',
        }
        invoice = account_invoice.create(invoice_vals)
        new_lines = self.env['account.invoice.line']
        for line in po.order_line:
            data = invoice._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(invoice)
            new_lines += new_line

        invoice.invoice_line_ids += new_lines
        invoice._onchange_partner_id()
        return invoice

    def test_default_journal_supplier(self):
        """Check that default journal is set correctly in the purchase invoices ."""

        purchase = self._get_purchase_order()
        partner = purchase.partner_id
        account_journal = self.env['account.journal']
        account_journals = account_journal.search([('type', '=', 'purchase')])
        if not account_journals:
            raise ValidationError(_('No purchase journals'))
        partner.write({'purchase_journal_id': account_journals[0].id})
        invoice = self._get_purchase_invoice(purchase)
        self.assertEqual(partner.purchase_journal_id.id, invoice.journal_id.id)
