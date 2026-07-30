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


def _get_l30_26_other_account(env, company, source_account):
    account = env.ref(
        "l10n_do.%s_%s" % (company.id, ACCOUNT_XMLID),
        raise_if_not_found=False,
    )
    if account:
        return account
    Account = env["account.account"]
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
        account = _get_l30_26_other_account(env, company, source_account)
        if not account:
            continue
        for tax in taxes:
            _set_tax_account(tax, account)
        _logger.info(
            "Company %s: art. 309 taxes moved to account %s",
            company.name,
            account.code,
        )


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    move_art_309_taxes_account(env)
