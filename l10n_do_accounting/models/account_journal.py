from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_do_fiscal_journal = fields.Boolean()

    payment_form = fields.Selection(
        [
            ("cash", "Efectivo"),
            ("bank", u"Cheque / Transferencia / Depósito"),
            ("card", u"Tarjeta Crédito / Débito"),
            ("credit", u"A Crédito"),
            ("swap", "Permuta"),
            ("bond", "Bonos o Certificados de Regalo"),
            ("others", "Otras Formas de Venta"),
        ],
        string="Payment Form",
    )
