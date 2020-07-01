from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_for_credit_notes = fields.Boolean(
        help="This payment method is for credit note", default=False
    )
