
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
