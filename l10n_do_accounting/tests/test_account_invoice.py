

from datetime import timedelta as td

from odoo import fields
from .common import AccountInvoiceCommon, environment


class AccountInvoiceTests(AccountInvoiceCommon):

    def test_001_invoice_fiscal_sequence_id(self):
        """
        Checks invoices gets the right fiscal_sequence_id
        when created
        """

        # Customer invoice (out_invoice)
        invoice_1_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'fiscal_type_id': self.fiscal_type_fiscal,
        })
        self.assertEqual(invoice_1_id.fiscal_sequence_id.id,
                         self.seq_fiscal)

        # Vendor bill (in_invoice)
        invoice_2_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_2,
            'fiscal_type_id': self.fiscal_type_informal,
            'type': 'in_invoice',
        })
        self.assertEqual(invoice_2_id.fiscal_sequence_id.id,
                         self.seq_informal)

        # Customer refund
        invoice_3_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_3,
            'type': 'out_refund',
        })
        self.assertEqual(invoice_3_id.fiscal_sequence_id.id,
                         self.seq_credit_note)

        # Customer debit note
        invoice_4_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_4,
            'type': 'out_invoice',
            'is_debit_note': True,
        })
        self.assertEqual(invoice_4_id.fiscal_sequence_id.id,
                         self.seq_debit_note)

    def test_002_date_invoice_expired_sequence(self):
        """
        Check that an invoice which date is >= fiscal sequence expiration
        date does not get any fiscal sequence
        """

        invoice_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'fiscal_type_id': self.fiscal_type_fiscal,
            'date_invoice': fields.Date.today() + td(weeks=156)
        })
        self.assertFalse(invoice_id.fiscal_sequence_id)

    def test_003_onchange_journal_id(self):
        """
        After create a new fiscal invoice, if journal is changed to a
        non fiscal one, fiscal_type_id and fiscal_sequence_id must be
        removed
        """

        invoice_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'fiscal_type_id': self.fiscal_type_fiscal,
        })

        no_fiscal_journal_id = self.journal_obj.create({
            'name': 'No fiscal Sale journal',
            'type': 'sale',
            'code': 'NFSJ',
        })
        invoice_id.journal_id = no_fiscal_journal_id.id
        invoice_id._onchange_journal_id()

        self.assertFalse(invoice_id.fiscal_type_id)
        self.assertFalse(invoice_id.fiscal_sequence_id)

    def test_004_onchange_partner_id(self):
        """
        When creating a new one or changing invoice partner_id,
        if not fiscal_type_id, invoice fiscal_type_id must be
        partner_id sale_fiscal_type_id
        """

        invoice_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'fiscal_type_id': self.fiscal_type_fiscal,
        })
        invoice_id.write({'fiscal_type_id': False,
                          'partner_id': self.partner_demo_4})
        invoice_id._onchange_partner_id()

        partner_id = self.partner_obj.browse(self.partner_demo_4)
        self.assertEqual(invoice_id.fiscal_type_id.id,
                         partner_id.sale_fiscal_type_id.id)

    def test_005_fiscal_type_journal(self):
        """
        When changing a draft invoice fiscal type to a one which
        have a journal, invoice journal must me fiscal type journal
        """

        consumo_journal_id = self.journal_obj.create({
            'name': 'Consumo Sale journal',
            'type': 'sale',
            'code': 'CSJ',
        })
        fiscal_type_consumo = self.fiscal_type_obj.browse(
            self.fiscal_type_consumo)
        fiscal_type_consumo.journal_id = consumo_journal_id.id

        invoice_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'fiscal_type_id': self.fiscal_type_fiscal,
        })
        invoice_id.fiscal_type_id = self.fiscal_type_consumo
        invoice_id._onchange_fiscal_type()

        self.assertEqual(invoice_id.journal_id.id,
                         fiscal_type_consumo.journal_id.id)

    def test_006_invoice_fiscal_type_expense_type(self):
        """
        When creating a new vendor bill or changing the partner
        to an existing one, fiscal_type_id and expense_type must
        come from the partner
        """

        invoice_id = self.invoice_obj.create({
            'partner_id': self.partner_demo_4,
            'type': 'in_invoice',
        })
        invoice_id.partner_id = self.partner_demo_5
        invoice_id._onchange_partner_id()

        partner_id = self.partner_obj.browse(self.partner_demo_5)

        self.assertEqual(invoice_id.fiscal_type_id.id,
                         partner_id.purchase_fiscal_type_id.id)
        self.assertEqual(invoice_id.expense_type,
                         partner_id.expense_type)

    def test_007_invoice_fiscal_sequence_status(self):
        """
        Check invoice fiscal_sequence_status 'fiscal_ok'
        when it should
        """

        invoice_1 = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'fiscal_type_id': self.fiscal_type_fiscal,
            'invoice_line_ids': self.invoice_line_data,
        })

        self.assertEqual(invoice_1.fiscal_sequence_status, 'fiscal_ok')

    def test_008_invoice_fiscal_sequence_status(self):
        """
        Check invoice fiscal_sequence_status 'almost_no_sequence'
        when it should
        """

        with environment() as env:
            env_sequence_id = env['account.fiscal.sequence'].search([
                ('fiscal_type_id', '=', self.fiscal_type_credito_fiscal),
                ('state', '=', 'active'),
            ])
            env_sequence_id.sequence_id.number_next_actual = 1

            # Consume it 66 times
            for n in range(66):
                env_sequence_id.get_fiscal_number()

        invoice_2 = self.invoice_obj.create({
            'partner_id': self.partner_demo_1,
            'fiscal_type_id': self.fiscal_type_fiscal,
            'invoice_line_ids': self.invoice_line_data,
        })
        self.assertEqual(invoice_2.fiscal_sequence_status,
                         'almost_no_sequence')

    def test_009_invoice_partner_sale_fiscal_type(self):
        """
        Check when out_invoice validate, if not partner_id.sale_fiscal_type_id,
        partner_id.sale_fiscal_type_id =  invoice.fiscal_type_id
        """

        partner_id = self.partner_obj.create({'name': 'Test Partner'})
        assert not partner_id.sale_fiscal_type_id

        invoice_id = self.invoice_obj.create({
            'partner_id': partner_id.id,
            'fiscal_type_id': self.fiscal_type_consumo,
            'invoice_line_ids': self.invoice_line_data,
        })
        invoice_id.action_invoice_open()

        self.assertEqual(partner_id.sale_fiscal_type_id.id,
                         self.fiscal_type_consumo)

# Account Invoice Tests

# TODO: when in_invoice validate, if not partner_id.purchase_fiscal_type_id,
#  partner_id.purchase_fiscal_type_id = invoice.fiscal_type_id and if not
#  partner_id.expense_type, partner_id.expense_type = invoice.expense_type

# TODO: when invoice validate, if fiscal_type_id.required_document and
#  not partner_id.vat, raise UserError

# TODO: when out_invoice, out_refund validate,
#  if fiscal_type_id != unico ingreso and amount_total >= 250,000
#  raise UserError

# TODO: a random number of random types invoices always get the
#  right NCF when validate

# TODO: fiscal customer refunds are created with all correct data

# TODO: fiscal vendor refunds are created with all correct data

# TODO: fiscal customer debit notes are created with all correct data

# TODO: fiscal vendor debit notes are created with all correct data
