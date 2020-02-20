
from odoo.tests.common import TransactionCase


class SaleOrderTests(TransactionCase):

    def setUp(self):
        super(SaleOrderTests, self).setUp()

        self.sale_obj = self.env['sale.order']
        self.invoice_obj = self.env['account.invoice']
        self.journal_obj = self.env['account.journal']

        journals = self.journal_obj.search([('type', '=', 'sale')])
        journals.write({'l10n_do_fiscal_journal': True})

        self.product_id = self.env.ref('product.product_product_24')

        self.order_line_data = [(0, 0, {
            'product_id': self.product_id.id,
            'product_uom_qty': 40.0,
            'name': 'product test 1',
            'price_unit': 2.27,
        })]

    def test_001_invoice_fiscal_type(self):
        """
        Check invoice created from sale order gets correct fiscal_type_id.
        CASE 1: Customer has a parent contact and parent contact is company.
        """

        parent_id = self.env.ref('l10n_do_accounting.res_partner_demo_4')
        customer = self.env.ref('l10n_do_accounting.res_partner_demo_5')
        customer.parent_id = parent_id.id

        sale_id = self.sale_obj.create({
            'partner_id': customer.id,
            'order_line': self.order_line_data,
        })
        sale_id.action_confirm()

        inv_id = sale_id.action_invoice_create()
        invoice = self.invoice_obj.browse(inv_id)

        self.assertEqual(
            invoice.fiscal_type_id.id,
            self.ref('l10n_do_accounting.fiscal_type_credito_fiscal'))

    def test_002_invoice_fiscal_type(self):
        """
        Check invoice created from sale order gets correct fiscal_type_id.
        CASE 2: Customer has not parent, has vat and fiscal type.
        """

        customer = self.env.ref('l10n_do_accounting.res_partner_demo_5')

        sale_id = self.sale_obj.create({
            'partner_id': customer.id,
            'order_line': self.order_line_data,
        })
        sale_id.action_confirm()

        inv_id = sale_id.action_invoice_create()
        invoice = self.invoice_obj.browse(inv_id)

        self.assertEqual(
            invoice.fiscal_type_id.id,
            self.ref('l10n_do_accounting.fiscal_type_consumo'))

    def test_003_invoice_fiscal_type(self):
        """
        Check invoice created from sale order gets correct fiscal_type_id.
        CASE 3: Customer has vat but not parent and fiscal type.
        """

        customer = self.env['res.partner'].create({'name': 'Test',
                                                   'vat': '12345678901'})

        sale_id = self.sale_obj.create({
            'partner_id': customer.id,
            'order_line': self.order_line_data,
        })
        sale_id.action_confirm()

        inv_id = sale_id.action_invoice_create()
        invoice = self.invoice_obj.browse(inv_id)

        self.assertEqual(
            invoice.fiscal_type_id.id,
            self.ref('l10n_do_accounting.fiscal_type_credito_fiscal'))

    def test_004_invoice_fiscal_type(self):
        """
        Check invoice created from sale order gets correct fiscal_type_id.
        CASE 3: Customer no vat, no parent and no fiscal type.
        """

        customer = self.env['res.partner'].create({'name': 'Test'})

        sale_id = self.sale_obj.create({
            'partner_id': customer.id,
            'order_line': self.order_line_data,
        })
        sale_id.action_confirm()

        inv_id = sale_id.action_invoice_create()
        invoice = self.invoice_obj.browse(inv_id)

        self.assertEqual(
            invoice.fiscal_type_id.id,
            self.ref('l10n_do_accounting.fiscal_type_consumo'))
