import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# The 3% art. 309 withholding taxes were posting to the accounts of
# their pre-law counterparts ("Otras Retenciones (N07-07)" and
# "Transferencias de Títulos y Propiedades"), which are tied to previous
# regulations. Give them their own payable account under Law 30-26,
# mirroring what was done for the 15% remittances withholding.
ART_309_TAXES = ("ret_3_income_person", "ret_3_income_transfer")
ACCOUNT_XMLID = "do_niif_21030311"
ACCOUNT_CODE = "21030311"
ACCOUNT_NAME = "Otras Retenciones (L30-26)"


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = %s
          AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def _unknown_required_columns(env, model_name, table):
    # Modules loading after this one add columns to the table (asset
    # management, withholding on payment, ...). Their fields are unknown
    # to the registry while this script runs, so copy() cannot fill them
    # and a required column would break the INSERT.
    known = set(["id"])
    for name, field in env[model_name]._fields.items():
        if field.store:
            known.add(name)
    env.cr.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
          AND is_nullable = 'NO'
          AND column_default IS NULL
        """,
        (table,),
    )
    return [c for (c,) in env.cr.fetchall() if c not in known]


def _drop_required(env, table, columns):
    for column in columns:
        env.cr.execute(
            'ALTER TABLE "%s" ALTER COLUMN "%s" DROP NOT NULL'
            % (table, column)
        )


def _restore_required(env, table, columns, copied_ids):
    # Give every new record the values of the record it was copied from,
    # then put the constraints back. A rollback restores them anyway,
    # since PostgreSQL keeps DDL transactional.
    if not columns:
        return
    assignments = ", ".join(
        '"%s" = src."%s"' % (column, column) for column in columns
    )
    for new_id, source_id in copied_ids:
        env.cr.execute(
            'UPDATE "%s" AS dst SET %s FROM "%s" AS src'
            " WHERE dst.id = %%s AND src.id = %%s"
            % (table, assignments, table),
            (new_id, source_id),
        )
    for column in columns:
        try:
            with env.cr.savepoint():
                env.cr.execute(
                    'ALTER TABLE "%s" ALTER COLUMN "%s" SET NOT NULL'
                    % (table, column)
                )
        except Exception:
            _logger.warning(
                "Could not restore the NOT NULL constraint of %s.%s",
                table,
                column,
            )


def _flag_withholding_account(env, account):
    # The withholding certification module adds these columns on the
    # account; it may not be installed and in any case loads after this
    # module, so its fields are unknown to the registry while this script
    # runs and must be set at SQL level.
    cr = env.cr
    if _column_exists(cr, "account_account", "is_l10n_do_withholding_account"):
        cr.execute(
            "UPDATE account_account"
            " SET is_l10n_do_withholding_account = TRUE"
            " WHERE id = %s",
            (account.id,),
        )
    if _column_exists(cr, "account_account", "l10n_do_legal_base"):
        cr.execute(
            "UPDATE account_account"
            " SET l10n_do_legal_base = %s"
            " WHERE id = %s",
            ("L30-26", account.id),
        )


def _get_tax_account(tax):
    if "invoice_repartition_line_ids" in tax._fields:
        line = tax.invoice_repartition_line_ids.filtered(
            lambda l: l.repartition_type == "tax" and l.account_id
        )[:1]
        return line.account_id
    return tax.account_id


def _set_tax_account(tax, account):
    if "invoice_repartition_line_ids" in tax._fields:
        lines = (
            tax.invoice_repartition_line_ids + tax.refund_repartition_line_ids
        ).filtered(lambda l: l.repartition_type == "tax")
        lines.write({"account_id": account.id})
    else:
        tax.write({"account_id": account.id, "refund_account_id": account.id})


def _get_l30_26_other_account(env, company, source_account, copied_accounts):
    account = env.ref(
        "l10n_do.%s_%s" % (company.id, ACCOUNT_XMLID),
        raise_if_not_found=False,
    )
    if account:
        return account
    Account = env["account.account"]
    # A previous run, or a manual fix, may have created the account
    # already without the external id: adopt it instead of adding a
    # second one under the next free code.
    account = Account.search(
        [("name", "=", ACCOUNT_NAME), ("company_id", "=", company.id)],
        limit=1,
    )
    if account:
        return account
    # The chart of accounts is the client's to extend: the canonical code
    # may already be taken by an unrelated account, so never adopt an
    # existing account by code - create a new one on the first free code.
    code = None
    for offset in range(90):
        candidate = str(21030311 + offset)
        if not Account.search(
            [("code", "=", candidate), ("company_id", "=", company.id)],
            limit=1,
        ):
            code = candidate
            break
    if not code:
        _logger.warning(
            "Company %s: no free code found for the Law 30-26 withholding "
            "account, keeping the current tax accounts",
            company.name,
        )
        return Account.browse()
    account = source_account.copy(
        default={"code": code, "name": ACCOUNT_NAME}
    )
    copied_accounts.append((account.id, source_account.id))
    _flag_withholding_account(env, account)
    if code == ACCOUNT_CODE:
        env["ir.model.data"].create(
            {
                "module": "l10n_do",
                "name": "%s_%s" % (company.id, ACCOUNT_XMLID),
                "model": "account.account",
                "res_id": account.id,
                "noupdate": True,
            }
        )
    else:
        _logger.warning(
            "Company %s: code %s was taken, Law 30-26 withholding account "
            "created with code %s",
            company.name,
            ACCOUNT_CODE,
            code,
        )
    return account


def move_art_309_taxes_account(env):
    account_columns = _unknown_required_columns(
        env, "account.account", "account_account"
    )
    _drop_required(env, "account_account", account_columns)
    copied_accounts = []
    for company in env["res.company"].search([]):
        taxes = env["account.tax"]
        for tax_name in ART_309_TAXES:
            tax = env.ref(
                "l10n_do.%s_%s" % (company.id, tax_name),
                raise_if_not_found=False,
            )
            if tax:
                taxes |= tax
        if not taxes:
            continue
        source_account = _get_tax_account(taxes[0])
        if not source_account:
            continue
        account = _get_l30_26_other_account(
            env, company, source_account, copied_accounts
        )
        if not account:
            continue
        for tax in taxes:
            _set_tax_account(tax, account)
        _logger.info(
            "Company %s: art. 309 taxes moved to account %s",
            company.name,
            account.code,
        )
    _restore_required(env, "account_account", account_columns, copied_accounts)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    move_art_309_taxes_account(env)
