import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate_ncf_expiration_date(env):
    companies = env["res.company"].search([("partner_id.country_id.code", "=", "DO")])
    for company in companies:
        fiscal_journals = env["account.journal"].search(
            [("l10n_latam_use_documents", "=", True), ("company_id", "=", company.id)]
        )
        for journal in fiscal_journals:
            # Create fiscal journal document types
            _logger.info("Creating %s journal document types" % journal.name)
            journal._l10n_do_create_document_types()
            env.cr.commit()
            # commit transaction so we can exec a query over news document types

    env.cr.execute(
        """
        SELECT EXISTS(
            SELECT
            FROM information_schema.columns
            WHERE table_name = 'l10n_latam_document_type'
            AND column_name = 'l10n_do_ncf_expiration_date'
        );
        """
    )
    if env.cr.fetchone()[0] or False:
        # Copy document type l10n_do_ncf_expiration_date to journals
        # document types l10n_do_ncf_expiration_date

        query = """
        UPDATE l10n_do_account_journal_document_type
        SET l10n_do_ncf_expiration_date = doc_type.l10n_do_ncf_expiration_date
        FROM l10n_latam_document_type doc_type
        WHERE l10n_latam_document_type_id = doc_type.id;
        """
        _logger.info(
            "Copying document type l10n_do_ncf_expiration_date to journals "
            "document types l10n_do_ncf_expiration_date"
        )
        env.cr.execute(query)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    migrate_ncf_expiration_date(env)
