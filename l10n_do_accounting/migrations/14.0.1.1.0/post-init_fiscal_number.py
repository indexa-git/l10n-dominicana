import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate_ref_field(env):
    query = """
    UPDATE account_move
    SET l10n_do_fiscal_number = ref
    WHERE l10n_do_fiscal_number IS NULL
    AND LENGTH(ref) IN (11, 13)
    AND ref LIKE 'B%' OR ref LIKE 'E%'
    AND type != 'entry'
    """
    env.cr.execute(query)
    _logger.info("Migrating ref field to l10n_do_fiscal_number")


def migrate(cr, version):

    env = api.Environment(cr, SUPERUSER_ID, {})
    migrate_ref_field(env)
