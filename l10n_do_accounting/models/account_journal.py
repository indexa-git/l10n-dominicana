
from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    fiscal_journal = fields.Boolean()

    # purchase_type = fields.Selection([
    #     ("normal", "Compras Fiscales"),
    #     ("minor", "Gastos Menores"),
    #     ("informal", "Comprobante de Compras"),
    #     ("exterior", "Pagos al Exterior"),
    #     ("import", "Importaciones"),
    #     ("others", "Otros (sin NCF)"),
    # ],
    #     string="Purchase Type",
    #     default="others",
    # )
    fiscal_type_id = fields.Many2one(
        'account.fiscal.type',
        string="Fiscal Type",
    )

    payment_form = fields.Selection(
        [("cash", "Efectivo"),
         ("bank", u"Cheque / Transferencia / Depósito"),
         ("card", u"Tarjeta Crédito / Débito"),
         ("credit", u"A Crédito"),
         ("swap", "Permuta"),
         ("bond", "Bonos o Certificados de Regalo"),
         ("others", "Otras Formas de Venta")],
        string="Payment Form",
    )
