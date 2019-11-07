
from contextlib import contextmanager

import odoo
from odoo import fields
from odoo.tests import common
from odoo.exceptions import ValidationError, MissingError
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

    def test_004_next_fiscal_number(self):
        """
        Next fiscal number shows the next complete fiscal number
        to be returned by the sequence
        """

        # check after sequence consume
        for i, _ in enumerate(range(10)):
            with environment() as env:
                sequence_id = env['account.fiscal.sequence'].browse(
                    self.fiscal_seq_credito_fiscal)
                next_fiscal_number = "%s%s" % (
                    sequence_id.fiscal_type_id.prefix,
                    str(sequence_id.sequence_id.number_next_actual).zfill(
                        sequence_id.fiscal_type_id.padding))

                sequence_id.get_fiscal_number()
                self.assertEqual(sequence_id.next_fiscal_number,
                                 next_fiscal_number)

    def test_005_sequence_start_default(self):
        """
        When on change fiscal_type_id, sequence start must be last active,
        depleted sequence end + 1
        """
        sequence_1_id = self.fiscal_sequence_obj.browse(
            self.fiscal_seq_credito_fiscal)

        sequence_2_id = self.fiscal_sequence_obj.create({
            'name': '7045195031',
            'fiscal_type_id': self.fiscal_type_consumo,
            'sequence_start': 141,
            'sequence_end': 732,
        })
        sequence_2_id.fiscal_type_id = self.fiscal_type_credito_fiscal
        sequence_2_id._onchange_fiscal_type_id()

        self.assertEqual(sequence_2_id.sequence_start,
                         sequence_1_id.sequence_end + 1)

    def test_006_active_sequence_uniqueness(self):
        """
        There must be only one active fiscal sequence per type
        """
        sequence_id = self.fiscal_sequence_obj.create({
            'name': '7045195031',
            'fiscal_type_id': self.fiscal_type_credito_fiscal,
            'sequence_start': 141,
            'sequence_end': 732,
            'remaining_percentage': 12,
        })

        with self.assertRaises(ValidationError):
            sequence_id._action_confirm()

    def test_007_active_sequence_uniqueness(self):
        """
        Check fiscal sequence does not have range overlap
        """
        sequence_id = self.fiscal_sequence_obj.create({
            'name': '7045195031',
            'fiscal_type_id': self.fiscal_type_credito_fiscal,
            'sequence_start': 101,
            'sequence_end': 150,
            'remaining_percentage': 12,
        })

        # Check sequence_end > sequence_start
        with self.assertRaises(ValidationError):
            sequence_id.write({'sequence_start': 350,
                               'sequence_end': 349})
            sequence_id._action_confirm()

        # Check no overlapping
        with self.assertRaises(ValidationError):
            sequence_id._action_confirm()

    def test_008_internal_sequence_delete(self):
        """
        Internal sequence must be deleted when fiscal sequence is deleted
        """

        sequence_id = self.fiscal_sequence_obj.browse(
            self.fiscal_seq_credito_fiscal)

        # Cancel before delete
        sequence_id._action_cancel()
        # Check state
        self.assertEqual(sequence_id.state, 'cancelled')
        self.assertEqual(sequence_id.sequence_id.active, False)

        sequence_id.unlink()
        with self.assertRaises(MissingError):
            bool(sequence_id.sequence_id)

    def test_009_fiscal_sequence_auto_expire(self):
        """
        Fiscal Sequence must change its state to 'expired' when
        validated or a cron runs _expire_sequences()
        """

        sequence_id = self.fiscal_sequence_obj.create({
            'name': '7045195031',
            'fiscal_type_id': self.fiscal_type_unico,
            'sequence_start': 101,
            'sequence_end': 150,
            'expiration_date': fields.Date.today(),
        })
        sequence_id._action_confirm()

        # Check state = 'expired'
        self.assertEqual(sequence_id.state, 'expired')

    def test_010_fiscal_sequence_sequence_vals(self):
        """
        Fiscal sequence's internal sequence must be created
        with correct values
        """

        # Cancel and delete an existing one
        sequence_id = self.fiscal_sequence_obj.browse(
            self.fiscal_seq_unico)
        sequence_id._action_cancel()
        sequence_id.unlink()

        sequence_unico_id = self.fiscal_sequence_obj.create({
            'name': '7045195031',
            'fiscal_type_id': self.fiscal_type_unico,
            'sequence_start': 1,
            'sequence_end': 10,
        })
        sequence_unico_id._action_confirm()

        # Check internal sequence vals
        self.assertRecordValues(
            sequence_unico_id.sequence_id,
            [{
                'implementation': 'standard',
                'padding': self.fiscal_type_obj.browse(
                    self.fiscal_type_unico).padding,
                'number_increment': 1,
                'number_next_actual': 1,
            }])

    def test_011_fiscal_sequence_sequence_vals(self):
        """
        When a new Fiscal sequence is validated, a internal sequence
        must be attached to it and its state 'active'
        """

        # Cancel and delete an existing one
        sequence_id = self.fiscal_sequence_obj.browse(
            self.fiscal_seq_unico)
        sequence_id._action_cancel()
        sequence_id.unlink()

        sequence_unico_id = self.fiscal_sequence_obj.create({
            'name': '7045195031',
            'fiscal_type_id': self.fiscal_type_unico,
            'sequence_start': 1,
            'sequence_end': 10,
        })
        sequence_unico_id._action_confirm()

        assert sequence_unico_id.sequence_id
        self.assertEqual(sequence_unico_id.state, 'active')

    def test_012_fiscal_sequence_auto_depleted(self):
        """
        When a new Fiscal sequence consume all its sequences,
        it must change its state to 'depleted'
        """
        # check after sequence consume

        sequence_id = False
        for i in range(100):
            with environment() as env:
                sequence_id = env['account.fiscal.sequence'].browse(
                    self.fiscal_seq_unico)
                sequence_id.get_fiscal_number()
            state = sequence_id.state

        # Check state
        self.assertEqual(sequence_id.state, 'depleted')

    # TODO: write a test to validate queued sequence auto active
