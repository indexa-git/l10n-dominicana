from odoo import models, fields, _
from odoo.exceptions import UserError


class ExpirationDateUpdateWizard(models.TransientModel):
    _name = "account.expiration.date.update_wizard"
    _description = "Account Expiration Date Update Wizard"

    document_type_id = fields.Many2one(
        "l10n_latam.document.type",
        "Document type",
        required=True,
    )
    l10n_do_ncf_expiration_date = fields.Date(
        string="New Expiration date",
        required=True,
    )

    def update_expiration_date(self):
        self.ensure_one()
        if (
            self.l10n_do_ncf_expiration_date
            < self.document_type_id.l10n_do_ncf_expiration_date
        ):
            raise UserError(_("You must set a date later than the current one"))

        self.document_type_id.sudo().write(
            {"l10n_do_ncf_expiration_date": self.l10n_do_ncf_expiration_date}
        )
