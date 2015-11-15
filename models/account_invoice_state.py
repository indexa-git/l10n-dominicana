# -*- coding: utf-8 -*-
from openerp import models, api, _, fields
from openerp.exceptions import UserError


class AccountInvoiceCancel(models.TransientModel):
    """
    This wizard will cancel the all the selected invoices.
    If in the journal, the option allow cancelling entry is not selected then it will give warning message.
    """

    _inherit = "account.invoice.cancel"
    _description = "Cancel the Selected Invoices"

    anulation_type = fields.Selection([
        ("01", u"01 - DETERIORO DE FACTURA PRE-IMPRESA"),
        ("02", u"02 - ERRORES DE IMPRESIÓN (FACTURA PRE-IMPRESA)"),
        ("03", u"03 - IMPRESIÓN DEFECTUOSA"),
        ("04", u"04 - DUPLICIDAD DE FACTURA"),
        ("05", u"05 - CORRECCIÓN DE LA INFORMACIÓN"),
        ("06", u"06 - CAMBIO DE PRODUCTOS"),
        ("07", u"07 - DEVOLUCIÓN DE PRODUCTOS"),
        ("08", u"08 - OMISIÓN DE PRODUCTOS"),
        ("09", u"09 - ERRORES EN SECUENCIA DE NCF")
    ], string=u"Tipo de anulación", required=True)

    @api.multi
    def invoice_cancel(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['account.invoice'].browse(active_ids):
            if record.state in ('cancel', 'paid'):
                raise UserError(_("Selected invoice(s) cannot be cancelled as they are already in 'Cancelled' or 'Done' state."))
            record.write({"anulation_type": self.anulation_type})
            record.signal_workflow('invoice_cancel')
        return {'type': 'ir.actions.act_window_close'}