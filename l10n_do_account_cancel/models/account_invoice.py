
from odoo import models, api, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_cancel(self):

        fiscal_invoice = self.filtered(
            lambda inv: inv.journal_id.fiscal_journal)
        if len(fiscal_invoice) > 1:
            raise ValidationError(
                _("You cannot cancel multiple fiscal invoices at a time."))

        if fiscal_invoice:
            action = self.env.ref(
                'l10n_do_account_cancel.action_account_invoice_cancel'
            ).read()[0]
            action['context'] = {'default_invoice_id': fiscal_invoice.id}
            return action

        return super(AccountInvoice, self).action_invoice_cancel()
