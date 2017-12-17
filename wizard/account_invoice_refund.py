# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2014 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    filter_refund = fields.Selection(
        selection_add=[('discount', 'Descuento'),
                       ('debit', u'Nota de Débito')])

    amount = fields.Float("Monto")
    account_id = fields.Many2one("account.account", string="Cuenta contable")
    supplier_ncf = fields.Char(string="NCF", size=19)
    invoice_type = fields.Char(default=lambda s: s._context.get("type", False))

    @api.onchange("filter_refund")
    def onchange_filter_refund(self):
        self.supplier_ncf = False
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
                origin_inv = self.env['account.invoice'].browse(origin_inv_id)
                refund = self.env['account.invoice'].browse(refund_id)
                vals = {'refund_reason': description}

                if mode in ("debit", "discount"):
                    new_line = refund.invoice_line_ids[0].copy(
                        {"product_id": False,
                         "name": self.description,
                         "account_id": self.account_id.id,
                         "quantity": 1,
                         "price_unit": self.amount})
                    vals.update({"invoice_line_ids": [(6, False,
                                                       [new_line.id])]})

                    if mode == "debit":
                        vals.update({"is_nd": True})

                        if refund.type == "out_refund":
                            vals.update({"type": "out_invoice"})

                        if refund.type == "in_refund":
                            vals.update({"type": "in_invoice",
                                         "expense_type": origin_inv.expense_type})

                            if self.supplier_ncf:
                                vals.update({"credit_note_supplier_ncf": self.supplier_ncf})

                refund.write(vals)

        return result

    @api.multi
    def invoice_refund(self):
        active_id = self._context.get("active_id", False)
        if active_id:
            invoice = self.env["account.invoice"].browse(active_id)

            if self.supplier_ncf:
                if self.filter_refund == 'debit' and self.supplier_ncf[9:11] != "03":
                    raise ValidationError(u"Las Notas de Débito deben ser tipo 03, este NCF no es de este tipo.")
                elif self.supplier_ncf[9:11] != "04":
                    raise ValidationError(u"Las Notas de Crédito deben ser tipo 04, este NCF no es de este tipo.")

            if self.supplier_ncf and invoice.journal_id.ncf_remote_validation:
                res = self.env["marcos.api.tools"].invoice_ncf_validation(self)
                if res is not True:
                    raise UserError(res[2])

        return super(AccountInvoiceRefund, self).invoice_refund()
