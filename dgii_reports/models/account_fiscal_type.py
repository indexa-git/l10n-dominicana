

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
    )
    sale_type = fields.Selection([
        ("final", "Consumer"),
        ("fiscal", "Fiscal Credit"),
        ("gov", "Gov"),
        ("special", "Special"),
        ("unico", "Single Income"),
        ("export", "Exports"),
    ],
    )
