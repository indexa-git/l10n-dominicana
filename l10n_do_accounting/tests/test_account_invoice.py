from datetime import timedelta as td

from odoo import fields
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from .common import AccountInvoiceCommon, environment


class AccountInvoiceTests(AccountInvoiceCommon):
    def test_001_invoice_l10n_latam_sequence_id(self):
        """
        Checks invoices gets the right l10n_latam_sequence_id
        when created
        """

        # Customer invoice (out_invoice)
        invoice_1_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
            }
        )
        self.assertEqual(invoice_1_id.l10n_latam_sequence_id.id, self.seq_fiscal)

        # Vendor bill (in_invoice)
        invoice_2_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_2,
                'l10n_latam_document_type_id': self.fiscal_type_informal,
                'type': 'in_invoice',
            }
        )
        self.assertEqual(invoice_2_id.l10n_latam_sequence_id.id, self.seq_informal)

        # Customer refund
        invoice_3_id = self.invoice_obj.create(
            {'partner_id': self.partner_demo_3, 'type': 'out_refund', }
        )
        self.assertEqual(invoice_3_id.l10n_latam_sequence_id.id, self.seq_credit_note)

        # Customer debit note
        invoice_4_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_4,
                'type': 'out_invoice',
                'is_debit_note': True,
            }
        )
        self.assertEqual(invoice_4_id.l10n_latam_sequence_id.id, self.seq_debit_note)

    def test_002_date_invoice_expired_sequence(self):
        """
        Check that an invoice which date is >= fiscal sequence expiration
        date does not get any fiscal sequence
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
                'date_invoice': fields.Date.today() + td(weeks=156),
            }
        )
        self.assertFalse(invoice_id.l10n_latam_sequence_id)

    def test_003_onchange_journal_id(self):
        """
        After create a new fiscal invoice, if journal is changed to a
        non fiscal one, l10n_latam_document_type_id and l10n_latam_sequence_id must be
        removed
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
            }
        )

        no_fiscal_journal_id = self.journal_obj.create(
            {'name': 'No fiscal Sale journal', 'type': 'sale', 'code': 'NFSJ', }
        )
        invoice_id.journal_id = no_fiscal_journal_id.id
        invoice_id._onchange_journal_id()

        self.assertFalse(invoice_id.l10n_latam_document_type_id)
        self.assertFalse(invoice_id.l10n_latam_sequence_id)

    def test_004_onchange_partner_id(self):
        """
        When creating a new one or changing invoice partner_id,
        if not l10n_latam_document_type_id, invoice l10n_latam_document_type_id must be
        partner_id sale_fiscal_type_id
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
            }
        )
        invoice_id.write(
            {'l10n_latam_document_type_id': False, 'partner_id': self.partner_demo_4}
        )
        invoice_id._onchange_partner_id()

        partner_id = self.partner_obj.browse(self.partner_demo_4)
        self.assertEqual(
            invoice_id.l10n_latam_document_type_id.id, partner_id.sale_fiscal_type_id.id
        )

    def test_005_fiscal_type_journal(self):
        """
        When changing a draft invoice fiscal type to a one which
        have a journal, invoice journal must me fiscal type journal
        """

        consumo_journal_id = self.journal_obj.create(
            {'name': 'Consumo Sale journal', 'type': 'sale', 'code': 'CSJ', }
        )
        fiscal_type_consumo = self.fiscal_type_obj.browse(self.fiscal_type_consumo)
        fiscal_type_consumo.journal_id = consumo_journal_id.id

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
            }
        )
        invoice_id.l10n_latam_document_type_id = self.fiscal_type_consumo
        invoice_id._onchange_fiscal_type()

        self.assertEqual(invoice_id.journal_id.id, fiscal_type_consumo.journal_id.id)

    def test_006_invoice_fiscal_type_l10n_do_expense_type(self):
        """
        When creating a new vendor bill or changing the partner
        to an existing one, l10n_latam_document_type_id and l10n_do_expense_type must
        come from the partner
        """

        invoice_id = self.invoice_obj.create(
            {'partner_id': self.partner_demo_4, 'type': 'in_invoice', }
        )
        invoice_id.partner_id = self.partner_demo_5
        invoice_id._onchange_partner_id()

        partner_id = self.partner_obj.browse(self.partner_demo_5)

        self.assertEqual(
            invoice_id.l10n_latam_document_type_id.id,
            partner_id.purchase_fiscal_type_id.id,
        )
        self.assertEqual(
            invoice_id.l10n_do_expense_type, partner_id.l10n_do_expense_type
        )

    def test_007_invoice_fiscal_sequence_status(self):
        """
        Check invoice fiscal_sequence_status 'fiscal_ok'
        when it should
        """

        invoice_1 = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
                'invoice_line_ids': self.invoice_line_data,
            }
        )

        self.assertEqual(invoice_1.fiscal_sequence_status, 'fiscal_ok')

    def test_008_invoice_fiscal_sequence_status(self):
        """
        Check invoice fiscal_sequence_status 'almost_no_sequence'
        when it should
        """

        with environment() as env:
            env_sequence_id = env['l10n_latam.document.pool'].search(
                [
                    (
                        'l10n_latam_document_type_id',
                        '=',
                        self.fiscal_type_credito_fiscal,
                    ),
                    ('state', '=', 'active'),
                ]
            )
            env_sequence_id.l10n_do_sequence_id.number_next_actual = 1

            # Consume it 66 times
            for n in range(66):
                env_sequence_id.get_fiscal_number()

        invoice_2 = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
                'invoice_line_ids': self.invoice_line_data,
            }
        )
        self.assertEqual(invoice_2.fiscal_sequence_status, 'almost_no_sequence')

    def test_009_invoice_partner_sale_fiscal_type(self):
        """
        Check when out_invoice validate, if not partner_id.sale_fiscal_type_id,
        partner_id.sale_fiscal_type_id =  invoice.l10n_latam_document_type_id
        """

        partner_id = self.partner_obj.create({'name': 'Test Partner'})
        assert not partner_id.sale_fiscal_type_id

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': partner_id.id,
                'l10n_latam_document_type_id': self.fiscal_type_consumo,
                'invoice_line_ids': self.invoice_line_data,
            }
        )
        invoice_id.action_invoice_open()

        self.assertEqual(partner_id.sale_fiscal_type_id.id, self.fiscal_type_consumo)

    def test_010_invoice_partner_purchase_fiscal_type_l10n_do_expense_type(self):
        """
        Check when in_invoice validate, if not partner_id.purchase_fiscal_type,
        partner_id.purchase_fiscal_type_id = invoice.l10n_latam_document_type_id"
        and if not partner_id.l10n_do_expense_type, "
        partner_id.l10n_do_expense_type = invoice.l10n_do_expense_type
        """

        partner_id = self.partner_obj.create(
            {'name': 'Test Partner', 'vat': '22400559607'}
        )
        assert not partner_id.purchase_fiscal_type_id
        assert not partner_id.l10n_do_expense_type

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': partner_id.id,
                'l10n_latam_document_type_id': self.fiscal_type_informal,
                'l10n_do_expense_type': '02',
                'invoice_line_ids': self.invoice_line_data,
                'type': 'in_invoice',
            }
        )
        invoice_id.action_invoice_open()

        self.assertEqual(
            partner_id.purchase_fiscal_type_id.id, self.fiscal_type_informal
        )
        self.assertEqual(partner_id.l10n_do_expense_type, '02')

    def test_011_is_vat_required_error(self):
        """
        Check when invoice validate, if l10n_latam_document_type_id.is_vat_required and
        not partner_id.vat, raise UserError
        """

        partner_id = self.partner_obj.create({'name': 'Test Partner'})

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': partner_id.id,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
                'invoice_line_ids': self.invoice_line_data,
            }
        )

        with self.assertRaises(UserError):
            invoice_id.action_invoice_open()

    def test_012_no_vat_partner_amount_total_limit(self):

        partner_id = self.partner_obj.create({'name': 'Test Partner'})

        account_id = (
            self.env['account.account']
            .search(
                [
                    (
                        'user_type_id',
                        '=',
                        self.env.ref('account.data_account_type_revenue').id,
                    )
                ],
                limit=1,
            )
            .id
        )
        invoice_line_data = [
            (
                0,
                0,
                {
                    'product_id': self.env.ref('product.product_product_1').id,
                    'quantity': 1.00,
                    'account_id': account_id,
                    'name': 'product test 1',
                    'price_unit': 250000,
                },
            )
        ]

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': partner_id.id,
                'l10n_latam_document_type_id': self.fiscal_type_consumo,
                'invoice_line_ids': invoice_line_data,
            }
        )

        with self.assertRaises(UserError):
            invoice_id.action_invoice_open()

        out_invoice_id = self.invoice_obj.create(
            {
                'partner_id': partner_id.id,
                'l10n_latam_document_type_id': self.fiscal_type_consumo,
                'invoice_line_ids': invoice_line_data,
            }
        )

        with self.assertRaises(UserError):
            out_invoice_id.action_invoice_open()

    def test_013_fiscal_customer_refund_percentage(self):
        """
        Check fiscal customer refunds (percentage) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
                'invoice_line_ids': self.invoice_line_data,
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {'active_ids': [invoice_id.id], 'active_id': invoice_id.id}
        ).create(
            {
                'refund_type': 'percentage',
                'filter_refund': 'refund',
                'description': 'Discount',
                'percentage': 10,
            }
        )
        refund_wizard_id.invoice_refund()

        credit_note_id = self.invoice_obj.search([('type', '=', 'out_refund')], limit=1)
        credit_note_id.action_invoice_open()

        cn_type = self.fiscal_type_obj.browse(self.fiscal_type_cn)

        self.assertEqual(
            credit_note_id.l10n_latam_document_type_id.id, self.fiscal_type_cn
        )
        self.assertEqual(str(credit_note_id.reference)[:3], cn_type.doc_code_prefix)
        self.assertEqual(credit_note_id.l10n_do_origin_ncf, invoice_id.reference)
        self.assertTrue(
            float_is_zero(
                credit_note_id.amount_total - (invoice_id.amount_total * 0.1),
                precision_digits=2,
            )
        )

    def test_014_fiscal_customer_refund_amount(self):
        """
        Check fiscal customer refunds (amount) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
                'invoice_line_ids': self.invoice_line_data,
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {'active_ids': [invoice_id.id], 'active_id': invoice_id.id}
        ).create(
            {
                'refund_type': 'fixed_amount',
                'filter_refund': 'refund',
                'description': 'Discount',
                'amount': 100,
            }
        )
        refund_wizard_id.invoice_refund()

        credit_note_id = self.invoice_obj.search([('type', '=', 'out_refund')], limit=1)
        credit_note_id.action_invoice_open()

        cn_type = self.fiscal_type_obj.browse(self.fiscal_type_cn)

        self.assertEqual(
            credit_note_id.l10n_latam_document_type_id.id, self.fiscal_type_cn
        )
        self.assertEqual(str(credit_note_id.reference)[:3], cn_type.doc_code_prefix)
        self.assertEqual(credit_note_id.l10n_do_origin_ncf, invoice_id.reference)
        self.assertEqual(credit_note_id.amount_total, 100)

    def test_015_fiscal_vendor_refund_percentage(self):
        """
        Check fiscal vendor refunds (percentage) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_informal,
                'invoice_line_ids': self.invoice_line_data,
                'type': 'in_invoice',
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {'active_ids': [invoice_id.id], 'active_id': invoice_id.id}
        ).create(
            {
                'refund_type': 'percentage',
                'filter_refund': 'refund',
                'description': 'Discount',
                'percentage': 10,
                'refund_reference': 'B0400000001',
            }
        )
        refund_wizard_id.invoice_refund()

        credit_note_id = self.invoice_obj.search([('type', '=', 'in_refund')], limit=1)
        credit_note_id.action_invoice_open()

        self.assertEqual(credit_note_id.reference, 'B0400000001')

        self.assertEqual(
            credit_note_id.l10n_latam_document_type_id.id, self.fiscal_type_cn_purchase
        )
        self.assertEqual(credit_note_id.l10n_do_origin_ncf, invoice_id.reference)
        self.assertTrue(
            float_is_zero(
                credit_note_id.amount_total - (invoice_id.amount_total * 0.1),
                precision_digits=2,
            )
        )

    def test_016_fiscal_vendor_refund_amount(self):
        """
        Check fiscal vendor refunds (amount) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_informal,
                'invoice_line_ids': self.invoice_line_data,
                'type': 'in_invoice',
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {'active_ids': [invoice_id.id], 'active_id': invoice_id.id}
        ).create(
            {
                'refund_type': 'fixed_amount',
                'filter_refund': 'refund',
                'description': 'Discount',
                'amount': 100,
                'refund_reference': 'B0400000001',
            }
        )
        refund_wizard_id.invoice_refund()

        credit_note_id = self.invoice_obj.search([('type', '=', 'in_refund')], limit=1)
        credit_note_id.action_invoice_open()

        self.assertEqual(credit_note_id.reference, 'B0400000001')

        self.assertEqual(
            credit_note_id.l10n_latam_document_type_id.id, self.fiscal_type_cn_purchase
        )
        self.assertEqual(credit_note_id.l10n_do_origin_ncf, invoice_id.reference)
        self.assertEqual(credit_note_id.amount_total, 100)

    def test_017_fiscal_customer_debit_note_percentage(self):
        """
        Check fiscal customer debit notes (percentage) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
                'invoice_line_ids': self.invoice_line_data,
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {
                'active_ids': [invoice_id.id],
                'active_id': invoice_id.id,
                'debit_note': 'out_debit',
            }
        ).create(
            {
                'refund_type': 'percentage',
                'filter_refund': 'refund',
                'description': 'Discount',
                'percentage': 10,
            }
        )
        refund_wizard_id.invoice_debit_note()

        debit_note_id = self.invoice_obj.search(
            [('type', '=', 'out_invoice'), ('is_debit_note', '=', True), ], limit=1
        )
        debit_note_id.action_invoice_open()

        dn_type = self.fiscal_type_obj.browse(self.fiscal_type_dn)

        self.assertEqual(
            debit_note_id.l10n_latam_document_type_id.id, self.fiscal_type_dn
        )
        self.assertEqual(str(debit_note_id.reference)[:3], dn_type.doc_code_prefix)
        self.assertEqual(debit_note_id.l10n_do_origin_ncf, invoice_id.reference)
        self.assertTrue(
            float_is_zero(
                debit_note_id.amount_total - (invoice_id.amount_total * 0.1),
                precision_digits=2,
            )
        )

    def test_018_fiscal_customer_debit_note_amount(self):
        """
        Check fiscal customer debit notes (amount) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_fiscal,
                'invoice_line_ids': self.invoice_line_data,
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {
                'active_ids': [invoice_id.id],
                'active_id': invoice_id.id,
                'debit_note': 'out_debit',
            }
        ).create(
            {
                'refund_type': 'fixed_amount',
                'filter_refund': 'refund',
                'description': 'Discount',
                'amount': 100,
            }
        )
        refund_wizard_id.invoice_debit_note()

        debit_note_id = self.invoice_obj.search(
            [('type', '=', 'out_invoice'), ('is_debit_note', '=', True), ], limit=1
        )
        debit_note_id.action_invoice_open()

        dn_type = self.fiscal_type_obj.browse(self.fiscal_type_dn)

        self.assertEqual(
            debit_note_id.l10n_latam_document_type_id.id, self.fiscal_type_dn
        )
        self.assertEqual(str(debit_note_id.reference)[:3], dn_type.doc_code_prefix)
        self.assertEqual(debit_note_id.l10n_do_origin_ncf, invoice_id.reference)
        self.assertEqual(debit_note_id.amount_total, 100)

    def test_019_fiscal_vendor_debit_note_percentage(self):
        """
        Check fiscal vendor debit notes (percentage) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_informal,
                'invoice_line_ids': self.invoice_line_data,
                'type': 'in_invoice',
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {
                'active_ids': [invoice_id.id],
                'active_id': invoice_id.id,
                'debit_note': 'in_debit',
            }
        ).create(
            {
                'refund_type': 'percentage',
                'filter_refund': 'refund',
                'description': 'Discount',
                'percentage': 10,
            }
        )
        refund_wizard_id.invoice_debit_note()

        debit_note_id = self.invoice_obj.search(
            [('type', '=', 'in_invoice'), ('is_debit_note', '=', True), ], limit=1
        )
        debit_note_id.action_invoice_open()

        self.assertEqual(
            debit_note_id.l10n_latam_document_type_id.id, self.fiscal_type_dn_purchase
        )
        self.assertEqual(debit_note_id.l10n_do_origin_ncf, invoice_id.reference)
        self.assertTrue(
            float_is_zero(
                debit_note_id.amount_total - (invoice_id.amount_total * 0.1),
                precision_digits=2,
            )
        )

    def test_020_fiscal_customer_debit_note_amount(self):
        """
        Check fiscal vendor debit notes (amount) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_informal,
                'invoice_line_ids': self.invoice_line_data,
                'type': 'in_invoice',
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {
                'active_ids': [invoice_id.id],
                'active_id': invoice_id.id,
                'debit_note': 'in_debit',
            }
        ).create(
            {
                'refund_type': 'fixed_amount',
                'filter_refund': 'refund',
                'description': 'Discount',
                'amount': 100,
            }
        )
        refund_wizard_id.invoice_debit_note()

        debit_note_id = self.invoice_obj.search(
            [('type', '=', 'in_invoice'), ('is_debit_note', '=', True), ], limit=1
        )
        debit_note_id.action_invoice_open()

        self.assertEqual(
            debit_note_id.l10n_latam_document_type_id.id, self.fiscal_type_dn_purchase
        )
        self.assertEqual(debit_note_id.l10n_do_origin_ncf, invoice_id.reference)
        self.assertEqual(debit_note_id.amount_total, 100)

    def test_021_fiscal_vendor_refund_percentage(self):
        """
        Check fiscal vendor refunds (full refund) are created with all
        correct data
        """

        invoice_id = self.invoice_obj.create(
            {
                'partner_id': self.partner_demo_1,
                'l10n_latam_document_type_id': self.fiscal_type_informal,
                'invoice_line_ids': self.invoice_line_data,
                'type': 'in_invoice',
            }
        )
        invoice_id.action_invoice_open()

        refund_wizard_id = self.invoice_refund_obj.with_context(
            {'active_ids': [invoice_id.id], 'active_id': invoice_id.id}
        ).create(
            {
                'refund_type': 'full_refund',
                'filter_refund': 'refund',
                'description': 'Full Refund',
                'refund_reference': 'B0400000001',
            }
        )

        # Refund wizard must be is_fiscal_refund == True because origin
        # invoice is fiscal
        assert refund_wizard_id.is_fiscal_refund

        refund_wizard_id.invoice_refund()
        credit_note_id = self.invoice_obj.search([('type', '=', 'in_refund')], limit=1)

        self.assertEqual(credit_note_id.reference, 'B0400000001')
