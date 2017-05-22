# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2014 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import requests

from odoo import models, api, fields, exceptions


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    filter_refund = fields.Selection(
        [('refund', u'Crear'),
         ('cancel', u'Cancelar'),
         ('modify', u'Modificar'),
         ('discount', u'Descuento'),
         ('nd', u'Nota de débido')
         ], default='refund', string='Opciones', required=True,
        help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled')
    amount = fields.Float(u"Monto")
    account_id = fields.Many2one(u"account.account", string=u"Cuenta contable")
    supplier_ncf = fields.Char(string="NCF nota de crédito", size=19)
    invoice_type = fields.Char(default=lambda s: s._context.get("type", False))

    @api.onchange("filter_refund")
    def onchange_filter_refund(self):
        self.supplier_ncf = False
        self.amount = False
        self.account_id = False

    @api.multi
    def compute_refund(self, mode='refund'):
        ctx = dict(self._context)
        if self.supplier_ncf:
            ctx.update({"credit_note_supplier_ncf": self.supplier_ncf})

        result = super(AccountInvoiceRefund, self.with_context(ctx)).compute_refund(mode)

        active_ids = self.env.context.get('active_ids')
        if not active_ids:  # pragma: no cover
            return result
        # An example of result['domain'] computed by the parent wizard is:
        # [('type', '=', 'out_refund'), ('id', 'in', [43L, 44L])]
        # The created refund invoice is the first invoice in the
        # ('id', 'in', ...) tupla
        created_inv = [x[2] for x in result['domain'] if x[0] == 'id' and x[1] == 'in'][0]
        if mode == 'modify':
            # Remove pairs ids, because they are new draft invoices
            del created_inv[1::2]

        if created_inv:
            description = self[0].description or ''
            for idx, refund_id in enumerate(created_inv):
                origin_inv_id = active_ids[idx]
                refund = self.env['account.invoice'].browse(refund_id)
                vals = {
                    'origin_invoice_ids': [(6, 0, [origin_inv_id])],
                    'refund_reason': description,
                }

                if mode in ("nd","discount"):

                    new_line = refund.invoice_line_ids[0].copy({"product_id": False,
                                                                "name": self.description,
                                                                "account_id": self.account_id.id,
                                                                "quantity": 1,
                                                                "price_unit": self.amount
                                                                })
                    vals.update({"invoice_line_ids": [(6, False, [new_line.id])]})

                    if mode == "nd":
                        vals.update({"is_nd": True})

                        if refund.type == "out_refund":
                            vals.update({"type": "out_invoice"})

                        if refund.type == "in_refund":
                            vals.update({"type": "in_invoice"})

                origin_inv = self.env['account.invoice'].browse(origin_inv_id)

                if self.supplier_ncf:
                    vals.update({"is_nd": self.supplier_ncf,
                                 "purchase_fiscal_type": origin_inv.purchase_fiscal_type})

                refund.write(vals)

                # Try to match refund invoice lines with original invoice lines
                refund.match_origin_lines(origin_inv)

        return result

    @api.multi
    def invoice_refund(self):
        active_id = self._context.get("active_id", False)
        if active_id:
            invoice = self.env["account.invoice"].browse(active_id)

            if invoice.state == "paid" and invoice.type in ('out_invoice', 'in_invoice') and self.filter_refund not in ('nd'):
                raise exceptions.ValidationError(u"No puede aplicar notas de crédito a una factura pagada.")

            if self.supplier_ncf:
                if self.filter_refund == 'nd' and self.supplier_ncf[9:-8] != "03":
                    raise exceptions.ValidationError(u"El NCF digitado no es válido para notas de débito.")
                elif self.supplier_ncf[9:-8] != "04":
                    raise exceptions.ValidationError(u"El NCF digitado no es válido para notas de crédito.")

            if self.supplier_ncf and invoice.journal_id.ncf_remote_validation:
                    request_params = self.env["marcos.api.tools"].get_marcos_api_request_params()
                    if request_params[0] == 1:
                        res = requests.get('{}/ncf/{}/{}'.format(request_params[1], invoice.partner_id.vat, self.supplier_ncf),proxies=request_params[2])
                        if res.status_code == 200 and not res.json().get("valid", False) == True:
                            return (500, u"Ncf invalido", u"El numero de comprobante fiscal no es valido! "
                                                          u"no paso la validacion en DGII, Verifique que el NCF y el RNC del "
                                                          u"proveedor esten correctamente digitados, si es de proveedor informal o de "
                                                          u"gasto menor vefifique si debe solicitar nuevos numero.")

        return super(AccountInvoiceRefund, self).invoice_refund()
