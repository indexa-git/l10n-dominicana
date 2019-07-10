# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

import logging

from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf
except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    filter_refund = fields.Selection(
        selection_add=[('discount', 'Descuento'), ('debit',
                                                   u'Nota de Débito')])

    amount = fields.Float("Monto")
    account_id = fields.Many2one("account.account", string="Cuenta contable")
    supplier_ncf = fields.Char(string="NCF", size=19)
    invoice_type = fields.Char(default=lambda s: s._context.get("type", False))
    journal_purchase_type = fields.Char(string="Tipo de Compra")

    @api.onchange("filter_refund")
    def onchange_filter_refund(self):
        invoice_id = self.env.context.get('active_ids')
        invoice = self.env['account.invoice'].browse(invoice_id[0])

        self.journal_purchase_type = invoice.journal_id.purchase_type
        self.supplier_ncf = False
        self.account_id = False

    @api.multi
    def compute_refund(self, mode='refund'):
        # TODO sale_fiscal_type are missing on refund wizard
        ctx = dict(self._context)
        if self.supplier_ncf:
            ctx.update({"credit_note_supplier_ncf": self.supplier_ncf})

        result = super(AccountInvoiceRefund,
                       self.with_context(ctx)).compute_refund(mode)

        active_ids = self.env.context.get('active_ids')
        if not active_ids:  # pragma: no cover
            return result
        # An example of result['domain'] computed by the parent wizard is:
        # [('type', '=', 'out_refund'), ('id', 'in', [43L, 44L])]
        # The created refund invoice is the first invoice in the
        # ('id', 'in', ...) tupla
        created_inv = [
            x[2] for x in result['domain'] if x[0] == 'id' and x[1] == 'in'
        ][0]

        if mode == 'modify':
            # Remove pairs ids, because they are new draft invoices
            del created_inv[1::2]

        if created_inv:
            for idx, refund_id in enumerate(created_inv):
                origin_inv_id = active_ids[idx]
                origin_inv = self.env['account.invoice'].browse(origin_inv_id)
                refund = self.env['account.invoice'].browse(refund_id)

                if origin_inv.type == "out_invoice" and \
                   origin_inv.journal_id.ncf_control:
                    refund.sale_fiscal_type = origin_inv.sale_fiscal_type

                if mode != "debit" and origin_inv.residual < self.amount:
                    raise ValidationError(
                        _("No puede hacer un descuento mayor al saldo "
                          "de la factura."))

                vals = {}
                if mode in ("debit", "discount"):
                    new_line = refund.invoice_line_ids[0].copy({
                        "product_id": False,
                        "name": self.description,
                        "account_id": self.account_id.id,
                        "quantity": 1,
                        "price_unit": self.amount
                    })
                    vals.update(
                        {"invoice_line_ids": [(6, False, [new_line.id])]})

                    if mode == "debit":

                        vals.update({"is_nd": True})

                        if refund.type == "out_refund":
                            vals.update({"type": "out_invoice"})
                            if result.get("domain", False):
                                result["domain"][0] = ('type', '=',
                                                       'out_invoice')

                        if refund.type == "in_refund":
                            vals.update({
                                "type": "in_invoice",
                                "expense_type": origin_inv.expense_type
                            })

                            if self.supplier_ncf:
                                vals.update({
                                    "credit_note_supplier_ncf":
                                        self.supplier_ncf
                                })

                refund.write(vals)

        return result

    @api.multi
    def invoice_refund(self):
        active_id = self._context.get("active_id", False)
        if active_id:
            invoice = self.env["account.invoice"].browse(active_id)

            if self.supplier_ncf:
                if self.filter_refund == 'debit' and self.supplier_ncf[
                        -10:-8] != '03':
                    raise ValidationError(
                        _(u"Las Notas de Débito deben ser tipo 03, este NCF "
                          "no es de este tipo."))
                elif self.filter_refund != 'debit' and self.supplier_ncf[
                        -10:-8] != '04':
                    raise ValidationError(
                        _(u"Las Notas de Crédito deben ser tipo 04, este NCF "
                          "no es de este tipo."))

            if self.supplier_ncf and invoice.journal_id.ncf_remote_validation:
                if not ncf.check_dgii(invoice.partner_id.vat,
                                      self.supplier_ncf):
                    raise UserError(_(
                        u"NCF NO pasó validación en DGII\n\n"
                        u"¡El número de comprobante *{}* del proveedor "
                        u"*{}* no pasó la validación en "
                        "DGII! Verifique que el NCF y el RNC del "
                        u"proveedor estén correctamente "
                        u"digitados, o si los números de ese NCF se "
                        "le agotaron al proveedor")
                        .format(self.supplier_ncf, invoice.partner_id.name))

        return super(AccountInvoiceRefund, self).invoice_refund()
