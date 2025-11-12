from odoo import models, fields, api, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    l10n_do_fiscal_number = fields.Char(
        "Fiscal Number",
    )
    l10n_do_origin_ncf = fields.Char(
        string="Modifies",
    )
