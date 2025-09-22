from odoo import models, fields, api, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    l10n_do_fiscal_number = fields.Char(
        "Fiscal Number",
        index=True,
        tracking=True,
        copy=False,
        help="Stored field equivalent of l10n_latam_document number",
    )
