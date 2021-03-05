import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def update_document_types_vat_required(env):
    l10n_do_ncf_types = [
        "fiscal",
        "debit_note",
        "informal",
        "special",
        "governmental",
        "export",
        "e-fiscal",
        "e-debit_note",
        "e-informal",
        "e-special",
        "e-governmental",
        "e-export",
    ]
    query = """
    UPDATE l10n_latam_document_type
    SET is_vat_required = 't'
    WHERE is_vat_required = 'f'
    AND l10n_do_ncf_type IN {ncf_types}
    AND country_id = {company}
    """
    env.cr.execute(
        query.format(
            ncf_types=tuple(l10n_do_ncf_types), company=env.ref("base.do").id
        )
    )
    _logger.log(25, "All Document Types set is_vat_required = True")


def migrate(cr, version):

    env = api.Environment(cr, SUPERUSER_ID, {})
    update_document_types_vat_required(env)
