from . import models
from . import wizard

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """
    Maps v12 ncf_manager module debit note
    fields to it's v13 homologue
    """

    env = api.Environment(cr, SUPERUSER_ID, {})

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

        Move = env["account.move"]
        for company in (
            env["res.company"]
            .search([])
            .filtered(lambda c: c.partner_id.country_id == env.ref("base.do").id)
        ):

            query = """
                SELECT move_name, origin_out
                FROM account_invoice
                WHERE origin_out IS NOT NULL
                AND state != 'draft'
                AND is_nd = 'true'
                AND company_id = %s;
                """
            env.cr.execute(query % company.id)
            result = env.cr.fetchall()
            result_len = len(result)
            for i, data in enumerate(result):
                move_name, origin_out = data
                invoice_id = Move.search(
                    [("name", "=", move_name), ("company_id", "=", company.id)]
                )
                if (
                    invoice_id
                    and str(invoice_id.ref)[1:3] in ("03", "33")
                    and (not invoice_id.debit_origin_id or not invoice_id.is_debit_note)
                ):
                    _logger.info(
                        "Migrating data for debit note %s - %s of %s"
                        % (invoice_id.ref, i, result_len)
                    )
                    debit_origin_id = Move.search(
                        [
                            ("ref", "=", origin_out.strip()),
                            ("company_id", "=", company.id),
                        ]
                    )
                    invoice_id.write(
                        {"debit_origin_id": debit_origin_id.id, "is_debit_note": True}
                    )
