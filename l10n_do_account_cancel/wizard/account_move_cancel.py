
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class AccountMoveCancel(models.TransientModel):
    """
    This wizard will cancel the all the selected invoices.
    If in the journal, the option allow cancelling entry is not selected then
    it will give warning message.
    """

    _name = "account.move.cancel"
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
            invoice.anulation_type = self.annulation_type
            invoice.action_cancel()
        return {'type': 'ir.actions.act_window_close'}
