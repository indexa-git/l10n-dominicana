import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate_ref_field(env):
    """
    ref   ---->   l10n_do_fiscal_number

    ref field is used from sale and purchase modules and may
    raise an error if you send anything else than an NCF/ECF.
    So we implement a new field l10n_do_fiscal_number to store
    fiscal number instead of using ref.

    Also compute l10n_do_sequence_prefix and l10n_do_sequence_number fields
    """

    query = """
    UPDATE account_move
    SET l10n_do_fiscal_number = ref,
    l10n_do_sequence_prefix=SUBSTRING(ref FROM 1 FOR 3),
    l10n_do_sequence_number=CAST(SUBSTRING(ref FROM 4 FOR 13) AS INTEGER)
    WHERE l10n_do_fiscal_number IS NULL
    AND LENGTH(ref) IN (11, 13)
    AND ref LIKE 'B%' OR ref LIKE 'E%'
    AND move_type != 'entry'
    """
    env.cr.execute(query)
    _logger.info("Migrating account_move ref field to l10n_do_fiscal_number")


def migrate_invoice_fields(env):
    """
    ncf_expiration_date   ---->   l10n_do_ncf_expiration_date
    """
    env.cr.execute(
        """
        SELECT EXISTS(
            SELECT
            FROM information_schema.columns
            WHERE table_name = 'account_move'
            AND column_name = 'ncf_expiration_date'
        );
        """
    )
    if env.cr.fetchone()[0] or False:
        query = """
        UPDATE account_move
        SET l10n_do_ncf_expiration_date = ncf_expiration_date;
        """
        _logger.info(
            """
            Migrating fields:
            ncf_expiration_date   ---->   l10n_do_ncf_expiration_date
            """
        )
        env.cr.execute(query)

        _logger.info("Dropping account_move deprecated columns")
        drop_query = """
        ALTER TABLE account_move
        DROP COLUMN IF EXISTS ncf_expiration_date,
        DROP COLUMN IF EXISTS cancellation_type;
        """
        env.cr.execute(drop_query)


def drop_sequence_fields(env):
    """
    Because v14 doesn't use ir.sequence for invoice fiscal sequence anymore,
    drop expiration_date field.
    """

    _logger.info("Dropping ir_sequence deprecated columns")
    drop_query = """
        ALTER TABLE ir_sequence
        DROP COLUMN IF EXISTS expiration_date;
        """
    env.cr.execute(drop_query)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    migrate_ref_field(env)
    migrate_invoice_fields(env)
    drop_sequence_fields(env)
