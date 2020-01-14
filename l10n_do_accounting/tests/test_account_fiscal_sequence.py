from odoo import fields
from .common import CommonSetup, environment
from odoo.exceptions import ValidationError, MissingError


class AccountFiscalSequenceBaseTests(CommonSetup):

    """
    The following tests are executed in a post-install context.
    This means that all fiscal sequence demo data are pre-loaded
    and are considered as existing data as every tests cursor
    is instantiated.
    """

    def test_001_fiscal_sequence_queue(self):
        """
        Validates only one sequence per type can be queue
        """

        l10n_do_sequence_id = self.fiscal_sequence_obj.create(
            {
                'name': '7045195031',
                'l10n_latam_document_type_id': self.fiscal_type_credito_fiscal,
                'sequence_start': 300,
                'sequence_end': 310,
            }
        )

        # Because there is one demo credito fiscal sequence queued,
        # sequence can_be_queue must be False
        self.assertEqual(l10n_do_sequence_id.can_be_queue, False)

    def test_002_warning_gap(self):
        """
        Warning gap is a value used to evaluate when fiscal
        sequence deplete warning should be shown. This test
        ensure this value will be always computed right.
        """
        l10n_do_sequence_id = self.fiscal_sequence_obj.create(
            {
                'name': '7045195031',
                'l10n_latam_document_type_id': self.fiscal_type_credito_fiscal,
                'sequence_start': 141,
                'sequence_end': 732,
                'remaining_percentage': 12,
            }
        )

        # Warning gap formula:
        # sequence_end - (sequence_start -1)
        # ----------------------------------
        #     remaining_percentage/100
        self.assertEqual(l10n_do_sequence_id.warning_gap, 71)

    def test_003_sequence_start_default(self):
        """
        When on change l10n_latam_document_type_id, sequence start must be last active,
        depleted sequence end + 1
        """
        sequence_1_id = self.fiscal_sequence_obj.browse(self.fiscal_seq_credito_fiscal)

        sequence_2_id = self.fiscal_sequence_obj.create(
            {
                'name': '7045195031',
                'l10n_latam_document_type_id': self.fiscal_type_consumo,
                'sequence_start': 141,
                'sequence_end': 732,
            }
        )
        sequence_2_id.l10n_latam_document_type_id = self.fiscal_type_credito_fiscal
        sequence_2_id._onchange_fiscal_type_id()

        self.assertEqual(sequence_2_id.sequence_start, sequence_1_id.sequence_end + 1)

    def test_004_active_sequence_uniqueness(self):
        """
        There must be only one active fiscal sequence per type
        """
        l10n_do_sequence_id = self.fiscal_sequence_obj.create(
            {
                'name': '7045195031',
                'l10n_latam_document_type_id': self.fiscal_type_credito_fiscal,
                'sequence_start': 141,
                'sequence_end': 732,
                'remaining_percentage': 12,
            }
        )

        with self.assertRaises(ValidationError):
            l10n_do_sequence_id._action_confirm()

    def test_005_active_sequence_uniqueness(self):
        """
        Check fiscal sequence does not have range overlap
        """
        l10n_do_sequence_id = self.fiscal_sequence_obj.create(
            {
                'name': '7045195031',
                'l10n_latam_document_type_id': self.fiscal_type_credito_fiscal,
                'sequence_start': 101,
                'sequence_end': 150,
                'remaining_percentage': 12,
            }
        )

        # Check sequence_end > sequence_start
        with self.assertRaises(ValidationError):
            l10n_do_sequence_id.write({'sequence_start': 350, 'sequence_end': 349})
            l10n_do_sequence_id._action_confirm()

        # Check no overlapping
        with self.assertRaises(ValidationError):
            l10n_do_sequence_id._action_confirm()

    def test_006_internal_sequence_delete(self):
        """
        Internal sequence must be deleted when fiscal sequence is deleted
        """

        l10n_do_sequence_id = self.fiscal_sequence_obj.browse(
            self.fiscal_seq_credito_fiscal
        )

        # Cancel before delete
        l10n_do_sequence_id._action_cancel()
        # Check state
        self.assertEqual(l10n_do_sequence_id.state, 'cancelled')
        self.assertEqual(l10n_do_sequence_id.l10n_do_sequence_id.active, False)

        l10n_do_sequence_id.unlink()
        with self.assertRaises(MissingError):
            bool(l10n_do_sequence_id.l10n_do_sequence_id)

    def test_007_fiscal_sequence_auto_expire(self):
        """
        Fiscal Sequence must change its state to 'expired' when
        validated or a cron runs _expire_sequences()
        """

        l10n_do_sequence_id = self.fiscal_sequence_obj.create(
            {
                'name': '7045195031',
                'l10n_latam_document_type_id': self.fiscal_type_unico,
                'sequence_start': 101,
                'sequence_end': 150,
                'expiration_date': fields.Date.today(),
            }
        )
        l10n_do_sequence_id._action_confirm()

        # Check state = 'expired'
        self.assertEqual(l10n_do_sequence_id.state, 'expired')

    def test_008_fiscal_sequence_sequence_vals(self):
        """
        Fiscal sequence's internal sequence must be created
        with correct values
        """

        # Cancel and delete an existing one
        l10n_do_sequence_id = self.fiscal_sequence_obj.browse(self.fiscal_seq_unico)
        l10n_do_sequence_id._action_cancel()
        l10n_do_sequence_id.unlink()

        sequence_unico_id = self.fiscal_sequence_obj.create(
            {
                'name': '7045195031',
                'l10n_latam_document_type_id': self.fiscal_type_unico,
                'sequence_start': 1,
                'sequence_end': 10,
            }
        )
        sequence_unico_id._action_confirm()

        # Check internal sequence vals
        self.assertRecordValues(
            sequence_unico_id.l10n_do_sequence_id,
            [
                {
                    'implementation': 'standard',
                    'padding': self.fiscal_type_obj.browse(
                        self.fiscal_type_unico
                    ).padding,
                    'number_increment': 1,
                    'number_next_actual': 1,
                }
            ],
        )

    def test_009_fiscal_sequence_sequence_vals(self):
        """
        When a new Fiscal sequence is validated, a internal sequence
        must be attached to it and its state 'active'
        """

        # Cancel and delete an existing one
        l10n_do_sequence_id = self.fiscal_sequence_obj.browse(self.fiscal_seq_unico)
        l10n_do_sequence_id._action_cancel()
        l10n_do_sequence_id.unlink()

        sequence_unico_id = self.fiscal_sequence_obj.create(
            {
                'name': '7045195031',
                'l10n_latam_document_type_id': self.fiscal_type_unico,
                'sequence_start': 1,
                'sequence_end': 10,
            }
        )
        sequence_unico_id._action_confirm()

        assert sequence_unico_id.l10n_do_sequence_id
        self.assertEqual(sequence_unico_id.state, 'active')


class AccountFiscalSequenceTransactionTests(CommonSetup):
    def test_010_sequence_transactions(self):
        """
        Check sequence remaining
        Check sequence next fiscal number
        Check sequence auto deplete
        Check queued sequence gets auto activated
        """

        with environment() as env:

            test_company = env['res.company'].search([('name', '=', 'Test Company')])
            if not test_company:
                test_company = env['res.company'].create({'name': 'Test Company'})

            l10n_do_sequence_id = env['l10n_latam.document.pool'].create(
                {
                    'name': '7045195031',
                    'l10n_latam_document_type_id': self.fiscal_type_credito_fiscal,
                    'sequence_start': 1,
                    'sequence_end': 10,
                    'company_id': test_company.id,
                }
            )
            l10n_do_sequence_id._action_confirm()
            self.assertEqual(l10n_do_sequence_id.sequence_remaining, 10)

            queued_sequence_id = env['l10n_latam.document.pool'].create(
                {
                    'name': 'queued',
                    'l10n_latam_document_type_id': self.fiscal_type_credito_fiscal,
                    'sequence_start': 11,
                    'sequence_end': 20,
                    'company_id': test_company.id,
                }
            )
            queued_sequence_id.action_queue()

        for i in range(10):
            with environment() as env:
                env_sequence_id = env['l10n_latam.document.pool'].search(
                    [
                        ('company_id', '=', test_company.id),
                        (
                            'l10n_latam_document_type_id',
                            '=',
                            self.fiscal_type_credito_fiscal,
                        ),
                        ('state', '=', 'active'),
                    ]
                )
                env_sequence_id.get_fiscal_number()
                next_fiscal_number = "%s%s" % (
                    env_sequence_id.l10n_latam_document_type_id.doc_code_prefix,
                    str(env_sequence_id.l10n_do_sequence_id.number_next_actual).zfill(
                        env_sequence_id.l10n_latam_document_type_id.padding
                    ),
                )

            # Check sequence_remaining
            self.assertEqual(
                env_sequence_id.sequence_remaining, env_sequence_id.sequence_end - i
            )
            # Check next_fiscal_number
            self.assertEqual(env_sequence_id.next_fiscal_number, next_fiscal_number)
        # Check state --> auto deplete
        self.assertEqual(env_sequence_id.state, 'depleted')

        # Check queued sequence gets auto activated
        with environment() as env:
            queued_sequence_id = env['l10n_latam.document.pool'].search(
                [('company_id', '=', test_company.id), ('name', '=', 'queued')]
            )
            self.assertEqual(queued_sequence_id.state, 'active')

        with environment() as env:
            env['l10n_latam.document.pool'].search(
                [
                    ('company_id', '=', test_company.id),
                    (
                        'l10n_latam_document_type_id',
                        '=',
                        self.fiscal_type_credito_fiscal,
                    ),
                ]
            ).unlink()
