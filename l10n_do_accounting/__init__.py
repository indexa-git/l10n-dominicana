from . import models
from . import wizard

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate_invoice_fields(env):
    """
    account_invoice  ---->  account_move
    reference               ref
    sale_fiscal_type        l10n_latam_document_type_id
    income_type             l10n_do_income_type
    expense_type            l10n_do_expense_type
    anulation_type          l10n_do_cancellation_type
    origin_out              l10n_do_origin_ncf
    """
    env.cr.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE  table_schema = 'public'
            AND    table_name   = 'account_invoice'
        );
        """
    )

    # if account_invoice table exist
    if env.cr.fetchone()[0] or False:

        _logger.info("Starting data migration from account_invoice to account_move")

        document_type_dict = {
            "01": env.ref("l10n_do_accounting.ncf_fiscal_client").id,
            "02": env.ref("l10n_do_accounting.ncf_consumer_supplier").id,
            "03": env.ref("l10n_do_accounting.ncf_debit_note_client").id,
            "04": env.ref("l10n_do_accounting.ncf_credit_note_client").id,
            "11": env.ref("l10n_do_accounting.ncf_informal_supplier").id,
            "12": env.ref("l10n_do_accounting.ncf_unique_client").id,
            "13": env.ref("l10n_do_accounting.ncf_minor_supplier").id,
            "14": env.ref("l10n_do_accounting.ncf_special_client").id,
            "15": env.ref("l10n_do_accounting.ncf_gov_client").id,
            "16": env.ref("l10n_do_accounting.ncf_export_client").id,
            "17": env.ref("l10n_do_accounting.ncf_exterior_supplier").id,
            "31": env.ref("l10n_do_accounting.ncf_fiscal_client").id,  # ECF
        }

        Move = env["account.move"]
        domain = [("country_id", "=", env.ref("base.do").id)]
        for company in env["res.company"].search(domain):

            # Sale invoices routine
            sales_journal = Move.with_context(
                default_type="out_invoice", default_company_id=company.id
            )._get_default_journal()

            sale_invoices = Move.search(
                [
                    ("journal_id", "=", sales_journal.id),
                    ("company_id", "=", company.id),
                    ("l10n_latam_document_type_id", "=", False),
                ]
            )
            sale_invoices_len = len(sale_invoices)

            for i, invoice in enumerate(sale_invoices):
                query = """
                    SELECT
                    reference, income_type, anulation_type, origin_out
                    FROM account_invoice
                    WHERE move_name = '%s'
                    AND is_nd = 'false'
                    AND state != 'draft';
                    """
                env.cr.execute(query % invoice.name)
                data = env.cr.fetchone()
                if data:
                    _logger.info(
                        "Migrating data for sale invoice %s - %s of %s"
                        % (data[0], i, sale_invoices_len)
                    )

                    ref = data[0].strip()
                    document_type_key = ref[1:3] if len(ref) in (11, 13) else ref[9:-8]
                    try:
                        document_type_id = document_type_dict[document_type_key]
                    except KeyError:
                        document_type_id = False

                    invoice.write(
                        {
                            "ref": ref,
                            "l10n_latam_document_type_id": document_type_id,
                            "l10n_do_income_type": data[1],
                            "l10n_do_cancellation_type": data[2],
                            "l10n_do_origin_ncf": data[3],
                        }
                    )

            sales_journal.with_context(allow_documents=True).write(
                {"l10n_latam_use_documents": True}
            )

            # Purchase invoices routine
            env.cr.execute(
                """
            SELECT id FROM account_journal
            WHERE purchase_type != 'others'
            AND company_id = %s
            """
                % company.id
            )

            purchase_journals = env["account.journal"].browse(
                [i[0] for i in env.cr.fetchall()]
            )
            for journal in purchase_journals:

                purchase_invoices = Move.search(
                    [
                        ("journal_id", "=", journal.id),
                        ("company_id", "=", company.id),
                        ("l10n_latam_document_type_id", "=", False),
                    ]
                )
                purchase_invoices_len = len(purchase_invoices)

                for i, invoice in enumerate(purchase_invoices):
                    query = """
                        SELECT
                        reference, expense_type, anulation_type, origin_out
                        FROM account_invoice
                        WHERE move_name = '%s'
                        AND is_nd = 'false'
                        AND state != 'draft';
                        """
                    env.cr.execute(query % invoice.name)
                    data = env.cr.fetchone()
                    if data:
                        _logger.info(
                            "Migrating data for purchase invoice %s - %s of %s"
                            % (data[0], i, purchase_invoices_len)
                        )

                        ref = data[0].strip()
                        document_type_key = (
                            ref[1:3] if len(ref) in (11, 13) else ref[9:-8]
                        )
                        try:
                            document_type_id = document_type_dict[document_type_key]
                        except KeyError:
                            document_type_id = False

                        invoice.write(
                            {
                                "ref": ref,
                                "l10n_latam_document_type_id": document_type_id,
                                "l10n_do_expense_type": data[1],
                                "l10n_do_cancellation_type": data[2],
                                "l10n_do_origin_ncf": data[3],
                            }
                        )

                journal.with_context(allow_documents=True).write(
                    {"l10n_latam_use_documents": True}
                )

            # Archive deprecated journals.
            # purchase_type in (minor, informal, exterior).
            # In v13 all purchase are supposed to use an unique journal which handle
            # all fiscal sequences.
            env.cr.execute(
                """
            SELECT id FROM account_journal
            WHERE type = 'purchase'
            AND purchase_type != 'normal'
            AND company_id = %s
            """
                % company.id
            )

            env["account.journal"].browse([i[0] for i in env.cr.fetchall()]).write(
                {"active": False}
            )


def post_init_hook(cr, registry):
    """
    This script maps and migrate data from v12 ncf_manager module to their
    homologue fields present in this module.

    Notice: this script won't convert your v12 database to a v13 one. This script
    only works if your database have been migrated by Odoo
    """

    env = api.Environment(cr, SUPERUSER_ID, {})

    migrate_invoice_fields(env)
