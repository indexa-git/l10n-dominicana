from odoo import models, fields, api, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    is_ecf_invoice = fields.Boolean(
        store=True,
    )
    l10n_do_ecf_security_code = fields.Char(string="e-CF Security Code", copy=False)
    l10n_do_ecf_sign_date = fields.Datetime(string="e-CF Sign Date", copy=False)
    l10n_do_electronic_stamp = fields.Char(
        string="Electronic Stamp",
        store=True,
    )
    l10n_do_ecf_edi_file = fields.Binary("ECF XML File", copy=False, readonly=True)

    l10n_do_ecf_edi_file_name = fields.Char(
        "ECF XML File Name", copy=False, readonly=True
    )
