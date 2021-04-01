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
    AND country_id = {country}
    """
    env.cr.execute(
        query.format(
            ncf_types=tuple(l10n_do_ncf_types), country=env.ref("base.do").id
        )
    )
    _logger.info("All Document Types set is_vat_required = True")


def log_missing_partner_vat_invoices(env):
    query = """
    SELECT move.id
    FROM account_move AS move
    JOIN account_journal AS journal
    ON (journal.id = move.journal_id)
    JOIN res_partner AS partner
    ON (partner.id = move.partner_id)
    JOIN l10n_latam_document_type as latam_document
    ON (latam_document.id = move.l10n_latam_document_type_id)
    WHERE journal.l10n_latam_use_documents = 't'
    AND latam_document.is_vat_required = 't'
    AND move.company_id = {company}
    AND
    (
        (partner.vat IS NULL)
        OR (COALESCE(TRIM(vat), '') = '')
    );
    """
    domain = [("partner_id.country_id", "=", env.ref("base.do").id)]
    for company in env["res.company"].search(domain):
        env.cr.execute(query.format(company=company.id))
        moves = env["account.move"].browse([r[0] for r in env.cr.fetchall()])
        names = moves.partner_id.mapped("name")
        for name in names:
            _logger.info(
                "Company {company} Partner {name} has not vat".format(
                    company=company.name, name=name
                )
            )


def migrate(cr, version):

    env = api.Environment(cr, SUPERUSER_ID, {})
    update_document_types_vat_required(env)
    log_missing_partner_vat_invoices(env)
