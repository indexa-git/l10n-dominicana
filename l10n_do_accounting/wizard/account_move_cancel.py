
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

    cancellation_type = fields.Selection(
        selection=lambda self: self.env[
            'account.move']._get_l10n_do_cancellation_type(),
        string="Cancellation Type",
        copy=False,
    )
    is_ecf_invoice = fields.Boolean(
        default=lambda self: self.env.user.company_id.l10n_do_ecf_issuer,
    )
    l10n_do_ecf_cancellation_type = fields.Selection(
        selection=lambda self: self.env[
            'account.move']._get_l10n_do_ecf_cancellation_type(),
        string='e-CF Cancellation Type',
        copy=False,
    )

    def move_cancel(self):

        if not any([self.l10n_do_ecf_cancellation_type, self.cancellation_type]):
            raise UserError(_("A cancellation type must be selected."))

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
            if self.is_ecf_invoice:
                invoice.l10n_do_ecf_cancellation_type = \
                    self.l10n_do_ecf_cancellation_type
            else:
                invoice.cancellation_type = self.cancellation_type
            invoice.write({'state': 'cancel'})
        return {'type': 'ir.actions.act_window_close'}
