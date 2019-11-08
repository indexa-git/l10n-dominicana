
from odoo.tests.common import TransactionCase


class AccountFiscalSequenceCommon(TransactionCase):

    def setUp(self):
        super(AccountFiscalSequenceCommon, self).setUp()

        self.fiscal_sequence_obj = self.env['account.fiscal.sequence']
        self.fiscal_type_obj = self.env['account.fiscal.type']
        self.fiscal_seq_credito_fiscal = self.ref(
            'l10n_do_accounting.credito_fiscal_demo')
        self.fiscal_seq_unico = self.ref(
            'l10n_do_accounting.unico_demo')
        self.fiscal_type_credito_fiscal = self.ref(
            'l10n_do_accounting.fiscal_type_credito_fiscal')
        self.fiscal_type_consumo = self.ref(
            'l10n_do_accounting.fiscal_type_consumo')
        self.fiscal_type_unico = self.ref(
            'l10n_do_accounting.fiscal_type_unico')


class AccountInvoiceCommon(TransactionCase):

    def setUp(self):
        super(AccountInvoiceCommon, self).setUp()

        self.invoice_obj = self.env['account.invoice']
        self.journal_obj = self.env['account.journal']

        self.sale_journal = False
        self.purchase_journal = False

        # Setup Fiscal Journals
        for journal in self.journal_obj.search(
                [('type', 'in', ('sale', 'purchase'))]):
            journal.fiscal_journal = True
            if journal.type == 'sale':
                self.sale_journal = journal
            else:
                self.purchase_journal = journal

        # Demo partners
        self.partner_demo_1 = self.ref('l10n_do_accounting.res_partner_demo_1')
        self.partner_demo_2 = self.ref('l10n_do_accounting.res_partner_demo_2')
        self.partner_demo_3 = self.ref('l10n_do_accounting.res_partner_demo_3')
        self.partner_demo_4 = self.ref('l10n_do_accounting.res_partner_demo_4')

        # Demo fiscal sequence
        self.seq_fiscal = self.ref('l10n_do_accounting.credito_fiscal_demo')
        self.seq_consumo = self.ref('l10n_do_accounting.consumo_demo')
        self.seq_unico = self.ref('l10n_do_accounting.unico_demo')
        self.seq_informal = self.ref('l10n_do_accounting.informal_demo')
        self.seq_credit_note = self.ref('l10n_do_accounting.cn_demo')
        self.seq_debit_note = self.ref('l10n_do_accounting.dn_demo')

        # Demo fiscal type
        self.fiscal_type_fiscal = self.ref(
            'l10n_do_accounting.fiscal_type_credito_fiscal')
        self.fiscal_type_informal = self.ref(
            'l10n_do_accounting.fiscal_type_informal')
