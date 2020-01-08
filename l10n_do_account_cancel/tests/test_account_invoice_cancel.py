from odoo.tests.common import TransactionCase


class AccountInvoiceTests(TransactionCase):

    def setUp(self):
        super(AccountInvoiceTests, self).setUp()

        self.invoice_obj = self.env['account.invoice']
        self.journal_obj = self.env['account.journal']

        journals = self.journal_obj.search([('type', '=', 'sale')])
        journals.write({'l10n_do_fiscal_journal': True})

        self.partner_demo_1 = self.ref('l10n_do_accounting.res_partner_demo_1')

        account_id = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref(
                'account.data_account_type_revenue').id)], limit=1).id

        self.invoice_line_data = [
            (0, 0,
             {
                 'product_id': self.env.ref('product.product_product_1').id,
                 'quantity': 40.0,
                 'account_id': account_id,
                 'name': 'product test 1',
                 'price_unit': 2.27,
             })]

    def test_001_invoice_cancel_wizard(self):
        """
        Check Cancellation type wizard is raised when fiscal invoice is
        cancelled
        """

        invoice_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'invoice_line_ids': self.invoice_line_data
        })
        invoice_id.action_invoice_open()
        self.assertEqual(
            invoice_id.action_invoice_cancel()['id'],
            self.ref('l10n_do_account_cancel.action_account_invoice_cancel')
        )
