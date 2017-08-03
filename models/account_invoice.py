# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################

from odoo import models, fields, api, exceptions

import logging

_logger = logging.getLogger(__name__)

import requests


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice',
                 'type')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()

        if self.journal_id.purchase_type == 'informal':
            self.amount_tax = sum(
                line.amount for line in self.tax_line_ids if not line.tax_id.purchase_tax_type in ("isr", "ritbis"))
            self.amount_total = self.amount_untaxed + self.amount_tax

    @api.model_cr_context
    def _auto_init(self):
        self._sql_constraints = [
            ('number_uniq', 'unique(number, company_id, partner_id, journal_id, type)',
             'Invoice Number must be unique per Company!'),
        ]

        super(AccountInvoice, self)._auto_init()

    @api.multi
    @api.depends('currency_id', "date_invoice")
    def _get_rate(self):
        for rec in self:
            if not rec.is_company_currency:
                try:
                    rate = rec.currency_id.with_context(dict(self._context or {}, date=rec.date_invoice))
                    rec.invoice_rate = 1 / rate.rate
                    rec.rate_id = rate.res_currency_rate_id
                except:
                    pass

    @api.depends("currency_id")
    def _is_company_currency(self):
        for rec in self:
            if rec.currency_id == rec.company_id.currency_id:
                rec.is_company_currency = True
            else:
                rec.is_company_currency = False

    def _default_user_shop(self):

        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        if shop_user_config:
            return shop_user_config[0]
        else:
            return False

    @api.multi
    def match_origin_lines(self, origin_inv):
        for idx, line in enumerate(origin_inv.invoice_line_ids):
            try:
                # Protect this write, maybe refund invoice doesn't
                # have the same lines than original one
                self.invoice_line_ids[idx].write({
                    'origin_line_ids': [(6, 0, line.ids)],
                })
            except:  # pragma: no cover
                pass
        return True

    shop_id = fields.Many2one("shop.ncf.config", string=u"Prefijo NCF", required=False,
                              default=_default_user_shop, domain=lambda s: [('user_ids', '=', [s._uid])])

    ncf_control = fields.Boolean(related="journal_id.ncf_control")
    purchase_type = fields.Selection(related="journal_id.purchase_type")
    sale_fiscal_type = fields.Selection([
        ("final", u"Consumidor final"),
        ("fiscal", u"Para credito fiscal"),
        ("gov", u"Gubernamental"),
        ("special", u"Regimenes especiales"),
        ("unico", u"Unico ingreso")
    ], string="NCF para", default="final")
    purchase_fiscal_type = fields.Selection([
        ('01', u'01 - Gastos de personal'),
        ('02', u'02 - Gastos por trabajo, suministros y servicios'),
        ('03', u'03 - Arrendamientos'),
        ('04', u'04 - Gastos de Activos Fijos'),
        ('05', u'05 - Gastos de Representación'),
        ('06', u'06 - Otras Deducciones Admitidas'),
        ('07', u'07 - Gastos Financieros'),
        ('08', u'08 - Gastos Extraordinarios'),
        ('09', u'09 - Compras y Gastos que forman parte del Costo de Venta'),
        ('10', u'10 - Adquisiciones de Activos'),
        ('11', u'11 - Gastos de Seguro'),
    ], string=u"Tipo de gasto")
    anulation_type = fields.Selection([
        ("01", u"DETERIORO DE FACTURA PRE-IMPRESA"),
        ("02", u"ERRORES DE IMPRESIÓN (FACTURA PRE-IMPRESA)"),
        ("03", u"IMPRESIÓN DEFECTUOSA"),
        ("04", u"DUPLICIDAD DE FACTURA"),
        ("05", u"CORRECCIÓN DE LA INFORMACIÓN"),
        ("06", u"CAMBIO DE PRODUCTOS"),
        ("07", u"DEVOLUCIÓN DE PRODUCTOS"),
        ("08", u"OMISIÓN DE PRODUCTOS"),
        ("09", u"ERRORES EN SECUENCIA DE NCF")
    ], string=u"Tipo de anulación", copy=False)
    refund_reason = fields.Text(string="Refund reason")
    origin_invoice_ids = fields.Many2many(
        comodel_name='account.invoice', column1='refund_invoice_id',
        column2='original_invoice_id', relation='account_invoice_refunds_rel',
        string=u"Factura original", readonly=True,
        help=u"Factura original a la que se remite esta factura de reembolso")
    refund_invoice_ids = fields.Many2many(
        comodel_name='account.invoice', column1='original_invoice_id',
        column2='refund_invoice_id', relation='account_invoice_refunds_rel',
        string=u"Reembolso de facturas", readonly=True,
        help=u"Devolución de facturas creadas a partir de esta factura")

    is_company_currency = fields.Boolean(compute=_is_company_currency)
    rate_id = fields.Many2one("res.currency.rate", string=u"Tasa", compute=_get_rate)
    invoice_rate = fields.Monetary(string="Tasa", compute=_get_rate, currency_field='currency_id')
    purchase_type = fields.Selection([("normal", u"REQUIERE NCF"),
                                      ("minor", u"GASTO MENOR NCF GENERADO POR EL SISTEMA"),
                                      ("informal", u"PROVEEDORES INFORMALES NCF GENERADO POR EL SISTEMA"),
                                      ("exterior", u"PAGOS AL EXTERIOR NO REQUIRE NCF"),
                                      ("import", u"IMPORTACIONES NO REQUIRE NCF"),
                                      ("others", u"OTROS NO REQUIRE NCF")],
                                     string=u"Tipo de compra", default="normal", related="journal_id.purchase_type")
    is_nd = fields.Boolean()

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        super(AccountInvoice, self)._onchange_journal_id()

        if self.journal_id.type == 'purchase' and self.journal_id.purchase_type == "minor":
            self.partner_id = self.company_id.partner_id.id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id.parent_id:
            self.partner_id = self.partner_id.parent_id


        super(AccountInvoice, self)._onchange_partner_id()

        if self.partner_id:
            if self.type in ('out_invoice', 'out_refund'):
                self.sale_fiscal_type = self.partner_id.sale_fiscal_type
            else:
                self.purchase_fiscal_type = self.partner_id.purchase_fiscal_type

            if self.journal_id.type == 'purchase' and self.journal_id.purchase_type == "minor":
                self.partner_id = self.company_id.partner_id.id

            if self.type in ("out_invoice", "out_refund") and not self.partner_id.customer:
                self.partner_id.customer = True
            if self.type in ("in_invoice", "in_refund") and not self.partner_id.supplier:
                self.partner_id.supplier = True

    @api.onchange('sale_fiscal_type', 'purchase_fiscal_type')
    def _onchange_fiscal_type(self):
        if self.partner_id:
            if self.type in ('out_invoice', 'out_refund'):
                self.partner_id.write({'sale_fiscal_type': self.sale_fiscal_type})
                if self.sale_fiscal_type == "special":
                    self.fiscal_position_id = self.env.ref("ncf_manager.ncf_manager_special_fiscal_position")
            else:
                self.partner_id.write({'purchase_fiscal_type': self.purchase_fiscal_type})

    @api.onchange("shop_id")
    def onchange_shop_id(self):
        if self.type in ('out_invoice', 'out_refund'):
            self.journal_id = self.shop_id.journal_id.id

    @api.one
    @api.constrains("move_name")
    def constrains_move_name(self):
        if self.type in ("in_invoice", "in_refund") and not self.state == "draft":
            res = self.env["marcos.api.tools"].invoice_ncf_validation(self)
            if not res == True:
                _logger.warning(res)
                raise exceptions.ValidationError(res[2])

    @api.multi
    def action_invoice_open(self):
        msg = False
        self._compute_amount()
        for rec in self:
            if not rec.partner_id.sale_fiscal_type:
                rec.sale_fiscal_type = "final"
            if rec.type in ("out_invoice",
                            "out_refund") and rec.sale_fiscal_type != "final" and rec.journal_id.ncf_control and not rec.partner_id.vat:
                msg = u"El cliente [{}]{} no tiene RNC y es requerido para este tipo de factura.".format(
                    rec.partner_id.id, rec.partner_id.name)
            elif rec.type in (
                    "in_invoice", "in_refund") and rec.journal_id.purchase_type == "normal" and not rec.partner_id.vat:
                msg = u"El proveedor no tiene RNC y es requerido para este tipo de compra."

            if msg:
                raise exceptions.ValidationError(msg)

        return super(AccountInvoice, self).action_invoice_open()

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice=date_invoice,
                                                          date=date, description=description, journal_id=journal_id)
        if self._context.get("credit_note_supplier_ncf", False):
            res.update({"move_name": self._context["credit_note_supplier_ncf"]})
        return res

    @api.model
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()

        if self.journal_id.type == "purchase" and self.journal_id.purchase_type in (
                "informal") and not self._context.get("from_payment"):
            res_without_retention = []
            tax_ids = [tax["tax_line_id"] for tax in res if tax["tax_line_id"]]
            tax_ids = self.env["account.tax"].browse(tax_ids)
            retention_tax = tax_ids.filtered(lambda r: r.purchase_tax_type in ("ritbis", "isr",)).ids
            for value in res:
                if not value.get("tax_line_id") in retention_tax:
                    res_without_retention.append(value)
            return res_without_retention

        return res

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        # Monkey patch to calc tax accurate with the base on multixcurrency invoice

        if self.currency_id != self.company_id.currency_id:
            tax_dict = {}
            amount_total = 0
            invoice_line_account_account_id = [line.account_id.id for line in self.invoice_line_ids]
            for line in move_lines:

                if line[2].get("account_id") in invoice_line_account_account_id:
                    amount_total += line[2]["debit"] + line[2]["credit"]

                if line[2].get("tax_ids"):
                    for tax_id in line[2]["tax_ids"]:
                        tax_id = self.env["account.tax"].browse(tax_id[1])
                        if not tax_dict.get(tax_id.id):
                            tax_dict.update(
                                {tax_id.id: {"amount": line[2]["debit"] + line[2]["credit"],
                                             "rate": tax_id.amount / 100, "price_include": tax_id.price_include}})
                        else:
                            tax_dict[tax_id.id]["amount"] += line[2]["debit"] + line[2]["credit"]

            for line in move_lines:
                if line[2].get("tax_line_id"):
                    if line[2]["debit"] > 0:
                        line[2]["debit"] = tax_dict[line[2]["tax_line_id"]]["amount"] * \
                                           tax_dict[line[2]["tax_line_id"]]["rate"]
                        amount_total += line[2]["debit"]
                    else:
                        line[2]["credit"] = tax_dict[line[2]["tax_line_id"]]["amount"] * \
                                            tax_dict[line[2]["tax_line_id"]]["rate"]
                        amount_total += line[2]["credit"]

            for line in move_lines:
                if line[2].get("account_id") == self.account_id.id:
                    if line[2]["debit"] > 0:
                        line[2]["debit"] = amount_total
                    else:
                        line[2]["credit"] = amount_total

        return move_lines


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    origin_line_ids = fields.Many2many(
        comodel_name='account.invoice.line', column1='refund_line_id',
        column2='original_line_id', string=u"Línea de factura original",
        relation='account_invoice_line_refunds_rel',
        help=u"Línea de factura original a la que se refiere esta línea de factura de reembolso")
    refund_line_ids = fields.Many2many(
        comodel_name='account.invoice.line', column1='original_line_id',
        column2='refund_line_id', string=u"Reembolso de la línea de factura",
        relation='account_invoice_line_refunds_rel',
        help=u"Reembolso de las líneas de factura creadas a partir de esta línea de factura")
