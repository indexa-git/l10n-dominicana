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

    l10n_do_cancellation_type = fields.Selection(
        selection=lambda self: self.env[
            "account.move"
        ]._get_l10n_do_cancellation_type(),
        string="Cancellation Type",
        copy=False,
        required=True,
    )

    def move_cancel(self):
        context = dict(self._context or {})
        active_ids = context.get("active_ids", []) or []
        for invoice in self.env["account.move"].browse(active_ids):
            if invoice.state == "cancel":
                raise UserError(
                    _(
                        "Selected invoice(s) cannot be cancelled as they are "
                        "already in 'Cancelled' state."
                    )
                )
            if invoice.payment_state != "not_paid":
                raise UserError(
                    _(
                        "Selected invoice(s) cannot be cancelled as they are "
                        "already in 'Paid' state."
                    )
                )

            # we call button_cancel() so dependency chain is
            # not broken in other modules extending that function
            invoice.mapped("line_ids.analytic_line_ids").unlink()
            invoice.with_context(skip_cancel_wizard=True).button_cancel()
            invoice.l10n_do_cancellation_type = self.l10n_do_cancellation_type

        return {"type": "ir.actions.act_window_close"}
