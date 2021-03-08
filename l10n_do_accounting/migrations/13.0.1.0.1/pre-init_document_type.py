import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def update_document_types_not_vat_required(env):
    query = """
    UPDATE l10n_latam_document_type
    SET is_vat_required = 'f'
    WHERE is_vat_required = 't'
    AND country_id = {country}
    """
    env.cr.execute(query.format(country=env.ref("base.do").id))
    _logger.info("All Document Types set is_vat_required = False")


def migrate(cr, version):

    env = api.Environment(cr, SUPERUSER_ID, {})
    update_document_types_not_vat_required(env)
