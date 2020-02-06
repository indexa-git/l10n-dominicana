
from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountMoveCancel(models.TransientModel):
    """
    This wizard will cancel the all the selected invoices.
    If in the journal, the option allow cancelling entry is not selected then
    it will give warning message.
    """

    _name = "account.move.cancel"
    _description = "Cancel the Selected Invoice"

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

    def move_cancel(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for invoice in self.env['account.move'].browse(active_ids):
            if invoice.state == 'cancel':
                raise UserError(
                    _("Selected invoice(s) cannot be cancelled as they are "
                      "already in 'Cancelled' state."))
            if invoice.invoice_payment_state != 'not_paid':
                raise UserError(
                    _("Selected invoice(s) cannot be cancelled as they are "
                      "already in 'Paid' state."))
            invoice.anulation_type = self.anulation_type
            invoice.write({'state': 'cancel'})
        return {'type': 'ir.actions.act_window_close'}
