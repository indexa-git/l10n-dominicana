from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    is_debit_note = fields.Boolean()
