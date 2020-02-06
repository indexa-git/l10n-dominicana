
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    anulation_type = fields.Selection(
        [
            ("01", "01 - Pre-printed Invoice Impairment"),
            ("02", "02 - Printing Errors (Pre-printed Invoice)"),
            ("03", "03 - Defective Printing"),
            ("04", "04 - Correction of Product Information"),
            ("05", "05 - Product Change"),
            ("06", "06 - Product Return"),
            ("07", "07 - Product Omission"),
            ("08", "08 - NCF Sequence Errors"),
            ("09", "09 - Cessation of Operations"),
            ("10", "10 - Lossing or Hurting Of Countiaries"),
        ],
        string="Annulment Type",
        copy=False,
    )

    def button_cancel(self):

        fiscal_invoice = self.filtered(
            lambda inv: inv.l10n_latam_country_code == 'DO')

        if len(fiscal_invoice) > 1:
            raise ValidationError(
                _("You cannot cancel multiple fiscal invoices at a time."))

        if fiscal_invoice:
            action = self.env.ref(
                'l10n_do_account_cancel.action_account_move_cancel'
            ).read()[0]
            action['context'] = {'default_move_id': fiscal_invoice.id}
            return action

        return super(AccountMove, self).button_cancel()
