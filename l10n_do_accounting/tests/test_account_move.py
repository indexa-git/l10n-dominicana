
from odoo import tools
from odoo.tests.common import TransactionCase
from odoo.modules.module import get_module_resource

# TODO: test normal account move


class AccountMoveTest(TransactionCase):

    def _load(self, module, *args):
        tools.convert_file(
            self.cr, 'l10n_do_accounting',
            get_module_resource(module, *args), {}, 'init', False, 'test',
            self.registry._assertion_report)

    def setUp(self):
        super(AccountMoveTest, self).setUp()

        # Minimal accounting setup
        self._load('account', 'test', 'account_minimal_test.xml')

        company = self.env.user.company_id

        country_do = self.env.ref("base.do").id

        journal_purchase = self.env.ref("l10n_do_accounting.expenses_journal")

        journal_sale = self.env.ref("l10n_do_accounting.sales_journal")

        journal_entries = self.env.ref("l10n_do_accounting.miscellaneous_journal")

        company.write({
            'vat': '131793916',
            'country_id': country_do,
        })

        journal_purchase.write({
            'l10n_latam_use_documents': True
        })

        journal_sale.write({
            'l10n_latam_use_documents': True
        })

        journal_entries.write({
            'l10n_latam_use_documents': True
        })

        self.partner = self.env['res.partner'].create({
            'name': 'jimmy',
            'vat': '40229590076',
            'country_id': country_do,
        })

        self.product = self.env.ref("product.product_product_4")

    def create_invoice(self, type):

        inv = self.env['account.move'].with_context(type=type).create({
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {'product_id': self.product.id, 'quantity': 1, 'price_unit': 110.0})
            ],
        })
        inv.post()
        return inv

    def test_001_account_move_if_button_cancel(self):

        inv_1 = self.create_invoice('in_invoice')

        inv_2 = self.create_invoice('out_invoice')

        inv_3 = self.create_invoice('in_refund')

        inv_4 = self.create_invoice('out_refund')

        # self.assertEqual(inv_1.button_cancel(),)
        # self.assertEqual(inv_2.button_cancel(),)
        # self.assertEqual(inv_3.button_cancel(),)
        # self.assertEqual(inv_4.button_cancel(),)
    #
    # def test_002_account_move_button_cancel(self):
    #
    #     inv_5 = self.create_invoice('entry')
    #     inv_6 = self.create_invoice('out_receipt')
    #     inv_7 = self.create_invoice('in_receipt')
