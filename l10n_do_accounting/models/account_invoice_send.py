

from odoo import models, api


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoiceSend, self).default_get(fields)

        active_ids = self._context.get('active_ids')
        invoice_ids = self.env['account.invoice'].browse(active_ids)
        company_id = invoice_ids.mapped('company_id')[0]

        l10n_do_coa = self.env.ref('l10n_do.do_chart_template')
        if company_id.chart_template_id.id == l10n_do_coa.id:
            res.update({'template_id': self.env.ref(
                'l10n_do_accounting.l10n_do_email_template_edi_invoice').id})

        return res
