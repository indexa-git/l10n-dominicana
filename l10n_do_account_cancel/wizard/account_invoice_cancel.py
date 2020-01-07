
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class AccountInvoiceCancel(models.TransientModel):
    """
    This wizard will cancel the all the selected invoices.
    If in the journal, the option allow cancelling entry is not selected then
    it will give warning message.
    """

    _name = "account.invoice.cancel"
    _description = "Cancel the Selected Invoice"

    annulation_type = fields.Selection(
        [("01", "01 - Deterioro de Factura Pre-impresa"),
         ("02", "02 - Errores de Impresión (Factura Pre-impresa)"),
         ("03", u"03 - Impresión Defectuosa"),
         ("04", u"04 - Corrección de la Información"),
         ("05", "05 - Cambio de Productos"),
         ("06", u"06 - Devolución de Productos"),
         ("07", u"07 - Omisión de Productos"),
         ("08", "08 - Errores en Secuencia de NCF"),
         ("09", "09 - Por Cese de Operaciones"),
         ("10", u"10 - Pérdida o Hurto de Talonarios"),
         ],
        required=True,
        default=lambda self: self._context.get('annulation_type', '04'))

    @api.multi
    def invoice_cancel(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        # TODO: esto solo debe salir solo cuando la factura sea fiscal
        for record in self.env['account.invoice'].browse(active_ids):
            if record.state in ('cancel', 'paid', 'in_payment'):
                raise UserError(
                    _("Selected invoice(s) cannot be cancelled as they are "
                      "already in 'Cancelled' or 'Paid' state."))
            record.anulation_type = self.annulation_type
            record.action_cancel()
        return {'type': 'ir.actions.act_window_close'}
