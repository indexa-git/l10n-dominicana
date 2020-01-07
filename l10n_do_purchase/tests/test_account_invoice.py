
from odoo import fields
from odoo.tests.common import TransactionCase


class AccountInvoiceTests(TransactionCase):

    def setUp(self):
        super(AccountInvoiceTests, self).setUp()

        self.invoice_obj = self.env['account.invoice']
        self.journal_obj = self.env['account.journal']
        self.purchase_obj = self.env['purchase.order']

        self.purchase_journal = False

        for journal in self.journal_obj.search([('type', '=', 'purchase')]):
            journal.l10n_do_fiscal_journal = True
            self.purchase_journal = journal

        self.partner_demo_1 = self.ref('l10n_do_accounting.res_partner_demo_1')
        self.product_id = self.env.ref('product.product_product_1')

        self.order_line_data = [(0, 0, {
            'product_id': self.product_id.id,
            'product_qty': 40.0,
            'name': 'product test 1',
            'price_unit': 2.27,
            'date_planned': fields.Datetime.today(),
            'product_uom': self.product_id.uom_id.id,
        })]

    def test_001_invoice_name(self):
        """
        Checks invoices gets the right name when created
        from purchase order
        """

        ref = 'B0100000002'
        purchase_id = self.purchase_obj.create({
            'partner_id': self.partner_demo_1,
            'partner_ref': ref,
            'order_line': self.order_line_data,
        })
        purchase_id.button_confirm()
        invoice_id = self.invoice_obj.with_context(
            purchase_id.action_view_invoice()['context']).create({})

        invoice_id.purchase_order_change()

        self.assertEqual(invoice_id.name, ref)
        self.assertFalse(invoice_id.reference)
