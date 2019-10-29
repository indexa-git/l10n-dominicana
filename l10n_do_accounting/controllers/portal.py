

from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalAccount(CustomerPortal):

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public",
                website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None,
                                 report_type=None, download=False, **kw):

        try:
            invoice_sudo = self._document_check_access(
                'account.invoice', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        l10n_do_coa = request.env.ref('l10n_do.do_chart_template')
        chart_template_id = invoice_sudo.company_id.chart_template_id
        if report_type in ('html', 'pdf', 'text') and chart_template_id.id == \
                l10n_do_coa.id:
            return self._show_report(
                model=invoice_sudo,
                report_type=report_type,
                download=download,
                report_ref='l10n_do_accounting.l10n_do_account_invoice')

        return super(PortalAccount, self).portal_my_invoice_detail(
            invoice_id, access_token, report_type, download, **kw)
