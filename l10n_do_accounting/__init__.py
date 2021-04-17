from . import models
from . import wizard

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def get_document_type_dict(env):
    return {
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
        "31": env.ref("l10n_do_accounting.ecf_fiscal_client").id,  # ECF
        "34": env.ref("l10n_do_accounting.ecf_credit_note_client").id,  # ECF
    }


def migrate_sale_invoice_fields(env, company):

    document_type_dict = get_document_type_dict(env)
    Move = env["account.move"]

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
                    AND state != 'draft'
                    AND company_id = %s;
                    """
        env.cr.execute(query % (invoice.name, company.id))
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
                # Here we force a document type because database has
                # shitty data and can't automatically determine one
                document_type_id = env.ref(
                    "l10n_do_accounting.non_fiscal_import_supplier"
                ).id

            invoice._write(
                {
                    "ref": ref,
                    "l10n_latam_document_type_id": document_type_id,
                    "l10n_do_income_type": data[1],
                    "l10n_do_cancellation_type": data[2],
                    "l10n_do_origin_ncf": data[3],
                }
            )

    sales_journal._write({"l10n_latam_use_documents": True})
    sales_journal.with_context(use_documents=True)._l10n_do_create_document_sequences()


def migrate_purchase_invoice_fields(env, company):

    # Purchase invoices routine
    env.cr.execute(
        """
    SELECT id FROM account_journal
    WHERE type = 'purchase'
    AND purchase_type != 'others'
    AND company_id = %s
    """
        % company.id
    )

    purchase_journals = env["account.journal"].browse([i[0] for i in env.cr.fetchall()])
    Move = env["account.move"]
    document_type_dict = get_document_type_dict(env)

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
                        AND state != 'draft'
                        AND company_id = %s;
                        """
            env.cr.execute(query % (invoice.name, company.id))
            data = env.cr.fetchone()
            if data:
                _logger.info(
                    "Migrating data for purchase invoice %s - %s of %s"
                    % (data[0], i, purchase_invoices_len)
                )

                ref = data[0].strip().replace(" ", "") if data[0] is not None else ""
                if ref:
                    document_type_key = ref[1:3] if len(ref) in (11, 13) else ref[9:-8]
                    try:
                        document_type_id = document_type_dict[document_type_key]
                    except KeyError:
                        # Here we force a document type because database has
                        # shitty data and can't automatically determine one
                        document_type_id = (
                            document_type_dict["01"]
                            if invoice.type == "in_invoice"
                            else document_type_dict["04"]
                        )
                else:
                    continue

                invoice._write(
                    {
                        "ref": ref,
                        "l10n_latam_document_type_id": document_type_id,
                        "l10n_do_expense_type": data[1],
                        "l10n_do_cancellation_type": data[2],
                        "l10n_do_origin_ncf": data[3],
                    }
                )

        journal._write({"l10n_latam_use_documents": True})
        journal.with_context(use_documents=True)._l10n_do_create_document_sequences()


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

        for company in (
            env["res.company"]
            .search([])
            .filtered(lambda c: c.partner_id.country_id == env.ref("base.do"))
        ):

            migrate_sale_invoice_fields(env, company)
            migrate_purchase_invoice_fields(env, company)

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


def migrate_fiscal_sequences(env):
    """
    ir_sequence_date_range   ---->  ir_sequence
    number_next                     number_next_actual
    """
    env.cr.execute(
        """
        SELECT EXISTS(
            SELECT
            FROM information_schema.columns
            WHERE table_name = 'ir_sequence_date_range'
            AND column_name = 'sale_fiscal_type'
        );
        """
    )

    # if ir_sequence_date_range table has sale_fiscal_type column
    if env.cr.fetchone()[0] or False:
        _logger.info(
            "Starting data migration from ir_sequence_date_range to ir_sequence"
        )
        for company in (
            env["res.company"]
            .search([])
            .filtered(lambda c: c.partner_id.country_id == env.ref("base.do"))
        ):

            fiscal_journals = env["account.journal"].search(
                [
                    ("l10n_latam_use_documents", "=", True),
                    ("company_id", "=", company.id),
                ]
            )

            fiscal_sequences = env["ir.sequence"].search(
                [("l10n_latam_journal_id", "in", fiscal_journals.ids)]
            )

            sale_fiscal_type_dict = {
                "minor": "13",
                "exterior": "17",
                "credit_note": "04",
                "debit_note": "03",
                "final": "02",
                "unico": "12",
                "gov": "15",
                "special": "14",
                "fiscal": "01",
                "informal": "11",
            }

            env.cr.execute(
                """
                SELECT dr.sale_fiscal_type, dr.number_next
                FROM ir_sequence_date_range AS dr
                JOIN ir_sequence AS seq
                ON (dr.sequence_id = seq.id)
                WHERE dr.sale_fiscal_type IS NOT NULL
                AND seq.company_id = %s;
                """
                % company.id
            )

            for fiscal_type, number_next in env.cr.fetchall():

                sequence_ids = fiscal_sequences.filtered(
                    lambda fs: fs.l10n_latam_document_type_id.id
                    == dict(get_document_type_dict(env))[
                        sale_fiscal_type_dict[fiscal_type]
                    ]
                )
                if sequence_ids and sequence_ids[0].number_next_actual < number_next:
                    _logger.info(
                        "Setting up %s number_next_actual" % sequence_ids[0].name
                    )
                    sequence_ids.write({"number_next_actual": number_next})


def migrate_partner_fields(env):
    """
    expense_type ---> l10n_do_expense_type
    """
    env.cr.execute(
        """
        SELECT EXISTS(
            SELECT
            FROM information_schema.columns
            WHERE table_name = 'res_partner'
            AND column_name = 'expense_type'
        );
        """
    )

    # if res_partner table has expense_type column
    if env.cr.fetchone()[0] or False:
        _logger.info("Starting partner fields migration")
        env.cr.execute(
            """
            SELECT id, expense_type
            FROM res_partner
            WHERE l10n_do_expense_type IS NULL
            AND expense_type IS NOT NULL;
            """
        )
        for i, expense_type in env.cr.fetchall():
            partner_id = env["res.partner"].browse(i)
            _logger.info(
                "Setting up %s l10n_do_expense_type = %s"
                % (partner_id.name, expense_type)
            )
            partner_id.write({"l10n_do_expense_type": expense_type})


def post_init_hook(cr, registry):
    """
    This script maps and migrate data from v12 ncf_manager module to their
    homologue fields present in this module.

    Notice: this script won't convert your v12 database to a v13 one. This script
    only works if your database have been migrated by Odoo
    """

    env = api.Environment(cr, SUPERUSER_ID, {})

    migrate_invoice_fields(env)
    migrate_fiscal_sequences(env)
    migrate_partner_fields(env)
