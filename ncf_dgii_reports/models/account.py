from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    payment_form = fields.Selection(selection_add=[("nota_credito", "Notas de Credito"),
                                                   ("mixto", "Mixto")])
