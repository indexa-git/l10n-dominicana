from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_latam_use_documents = fields.Boolean(
        'Use Documents?', help="If active: will be using for legal invoicing (invoices, debit/credit notes)."
        " If not set means that will be used to register accounting entries not related to invoicing legal documents."
        " For Example: Receipts, Tax Payments, Register journal entries")

    l10n_do_payment_form = fields.Selection(
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