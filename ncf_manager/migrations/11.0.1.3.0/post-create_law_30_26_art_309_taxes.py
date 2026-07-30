import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# Law 30-26 raised the art. 309 withholding rate from 10% to 15% without
# amending art. 70 of Regulation 139-98, which keeps the 20% presumed
# base for technical services provided by individuals, so the effective
# withholding moves from 2% to 3% (confirmed by DGII, notice 10-26,
# effective July 1, 2026). The 2% taxes remain valid for operations
# prior to the law, so the 3% counterparts are created as new taxes.
# On databases where the previous Law 30-26 script already ran, only
# these two records are created; anything already existing is skipped
# by external id.
LAW_30_26_309_TAXES = [
    (
        "ret_3_income_person",
        "ret_2_income_person",
        {
            "name": "Retención 3% ISR a Físicas (L30-26)",
            "description": "-3% ISR",
            "amount": -3.0,
        },
    ),
    (
        "ret_3_income_transfer",
        "ret_2_income_transfer",
        {
            "name": "Retención 3% ISR a Físicas (con Materiales) (L30-26)",
            "description": "-3% ISR Mat.",
            "amount": -3.0,
        },
    ),
]


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


def create_law_30_26_art_309_taxes(env):
    ir_model_data = env["ir.model.data"]
    tax_columns = _unknown_required_columns(env, "account.tax", "account_tax")
    _drop_required(env, "account_tax", tax_columns)
    copied_taxes = []
    for company in env["res.company"].search([]):
        for new_name, source_name, values in LAW_30_26_309_TAXES:
            source = env.ref(
                "l10n_do.%s_%s" % (company.id, source_name),
                raise_if_not_found=False,
            )
            if not source:
                continue
            if env.ref(
                "l10n_do.%s_%s" % (company.id, new_name),
                raise_if_not_found=False,
            ):
                continue
            # On versions where taxes and tax groups carry a country,
            # country_id is a stored computed field: the copy recomputes
            # it from the company fiscal country while the tax group is
            # copied from the source. Legacy data can hold a mismatched
            # pair that would trip the tax group country constraint on
            # the new record, so make the pair explicit.
            if (
                "country_id" in source._fields
                and "country_id" in source.tax_group_id._fields
            ):
                country = source.tax_group_id.country_id or source.country_id
                if country:
                    values = dict(values, country_id=country.id)
            tax = env["account.tax"].search(
                [
                    ("name", "=", values["name"]),
                    ("company_id", "=", company.id),
                    ("type_tax_use", "=", source.type_tax_use),
                ],
                limit=1,
            )
            if not tax:
                tax = source.copy(default=values)
                copied_taxes.append((tax.id, source.id))
            ir_model_data.create(
                {
                    "module": "l10n_do",
                    "name": "%s_%s" % (company.id, new_name),
                    "model": "account.tax",
                    "res_id": tax.id,
                    "noupdate": True,
                }
            )
            _logger.info(
                "Company %s: created Law 30-26 tax %s", company.name, tax.name
            )
    _restore_required(env, "account_tax", tax_columns, copied_taxes)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    create_law_30_26_art_309_taxes(env)
