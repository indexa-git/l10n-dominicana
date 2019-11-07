
from contextlib import contextmanager

import odoo
from odoo.tests import common
from odoo.tests.common import TransactionCase

ADMIN_USER_ID = common.ADMIN_USER_ID


@contextmanager
def environment():
    """ Return an environment with a new cursor for the current database; the
        cursor is committed and closed after the context block.
    """
    registry = odoo.registry(common.get_db_name())
    with registry.cursor() as cr:
        yield odoo.api.Environment(cr, ADMIN_USER_ID, {})


class AccountFiscalSequenceTests(TransactionCase):

    """
    The following tests are executed in a post-install context.
    This means that all fiscal sequence demo data are pre-loaded
    and are considered as existing data as every tests cursor
    is instantiated.
    """

    def setUp(self):
        super(AccountFiscalSequenceTests, self).setUp()

        self.fiscal_sequence_obj = self.env['account.fiscal.sequence']
        self.fiscal_seq_credito_fiscal = self.ref(
            'l10n_do_accounting.credito_fiscal_demo')
        self.fiscal_type_credito_fiscal = self.ref(
            'l10n_do_accounting.fiscal_type_credito_fiscal')

    def test_001_fiscal_sequence_queue(self):
        """
        Validates only one sequence per type can be queue
        """

        sequence_id = self.fiscal_sequence_obj.create({
            'name': '7045195031',
            'fiscal_type_id': self.fiscal_type_credito_fiscal,
            'sequence_start': 300,
            'sequence_end': 310,
        })

        # Because there is one demo credito fiscal sequence queued,
        # sequence can_be_queue must be False
        self.assertEqual(sequence_id.can_be_queue, False)

    def test_002_warning_gap(self):
        """
        Warning gap is a value used to evaluate when fiscal
        sequence deplete warning should be shown. This test
        ensure this value will be always computed right.
        """
        sequence_id = self.fiscal_sequence_obj.create({
            'name': '7045195031',
            'fiscal_type_id': self.fiscal_type_credito_fiscal,
            'sequence_start': 141,
            'sequence_end': 732,
            'remaining_percentage': 12,
        })

        # Warning gap formula:
        # sequence_end - (sequence_start -1)
        # ----------------------------------
        #     remaining_percentage/100
        self.assertEqual(sequence_id.warning_gap, 71)

    def test_003_sequence_remaining(self):
        """
        Sequence remaining shows how many sequences are left
        """
        sequence_id = self.fiscal_sequence_obj.browse(
            self.fiscal_seq_credito_fiscal)

        # new sequence remaining check
        self.assertEqual(sequence_id.sequence_remaining, 100)

        # check after sequence consume
        for i, _ in enumerate(range(10)):
            with environment() as env:
                sequence_id = env['account.fiscal.sequence'].browse(
                    self.fiscal_seq_credito_fiscal)
                sequence_id.get_fiscal_number()
                self.assertEqual(sequence_id.sequence_remaining,
                                 sequence_id.sequence_end - i)

# Account Fiscal Sequence Tests

# TODO: next_fiscal_number is correctly computed
# TODO: default sequence_start is correctly computed
# TODO: unique active sequence ValidationError raised
# TODO: _validate_sequence_range() ValidationErrors raised
# TODO: internal sequence is deleted when fiscal sequence is deleted
# TODO: fiscal sequence is auto expired if expiration_date is today
# TODO: when a draft fiscal sequence is confirmed, a internal sequence
#  is created too with correct vals
# TODO: when a draft fiscal sequence is confirmed, a new internal sequence
#  is attached and state == 'active'
# TODO: when a fiscal sequence is cancelled, its internal sequence is set to
#  inactive and state == 'cancelled'
# TODO: a fiscal sequence is auto-depleted when its get out of available
#  sequences
# TODO: a fiscal sequence of random type always returns the correct combination
#  of prefix-padding-sequence string
