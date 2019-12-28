

from odoo import models, fields


class AccountFiscalType(models.Model):
    _inherit = 'account.fiscal.type'

    purchase_type = fields.Selection([
        ("normal", "Fiscal Purchase"),
        ("minor", "Minor expenses"),
        ("informal", "Purchase Document"),
        ("exterior", "Overseas Payments"),
        ("import", "Imports"),
        ("others", "Others (no NCF)"),
    ],
        default="others",
    )
