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


def create_law_30_26_art_309_taxes(env):
    ir_model_data = env["ir.model.data"]
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


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    create_law_30_26_art_309_taxes(env)
