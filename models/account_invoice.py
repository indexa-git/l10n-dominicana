# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
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
import json

from openerp import exceptions
import requests
from tools import is_ncf, _internet_on
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models, _

from datetime import datetime


import logging
_logger = logging.getLogger(__name__)

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _default_user_shop(self):
        shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
        return shop_user_config["shop_ids"][0]

    def _default_user_journal(self):
        if self._context.get("type", False) in ("out_invoice", "out_refound") or self._context.get("active_model",
                                                                                                   False) == "sale.order":
            shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()
            if not shop_user_config:
                raise exceptions.ValidationError("Los diarios de ventas no estan configurados corectamente.")
            else:
                return shop_user_config["sale_journal_ids"][0]
        elif self._context.get("type", False) in ("in_invoice", "in_refound"):
            res = False
            journal = self.env["account.journal"].search([('type', '=', 'purchase'), ('purchase_type', '=', 'normal')])
            if not journal:
                journal = self.env["account.journal"].search([('type', '=', 'purchase')])

            if journal:
                res = journal[0].id
            if not res:
                raise exceptions.ValidationError("Debe configurar diarios de compra.")
            else:
                return res

    @api.one
    def _get_total_discount(self):
        total_discount = 0.0
        for line in self.invoice_line_ids:
            total_discount += line.price_unit * ((line.discount or 0.0) / 100.0)
        self.total_discount = total_discount

    @api.one
    def _get_overdue_type(self):
        overdue = self.partner_id.issued_total - self.amount_total
        credit_available = self.partner_id.credit_limit - (self.partner_id.balance - self.amount_total)

        if self.amount_total > credit_available and overdue > 0:
            self.overdue_type = "overlimit_overdue"
        elif self.amount_total > credit_available:
            self.overdue_type = "overlimit"
        elif overdue > 0:
            self.overdue_type = "overdue"
        else:
            self.overdue_type = "none"

    @api.one
    @api.depends("currency_id")
    def _get_rate(self):
        if self.currency_id:
            if self.currency_id.id != self.company_id.currency_id.id:
                self._cr.execute("""SELECT rate FROM res_currency_rate
                                   WHERE currency_id = %s
                                     AND name = %s
                                     AND (company_id is null
                                         OR company_id = %s)
                                ORDER BY company_id, name desc LIMIT 1""",
                               (self.currency_id.id, self.date_invoice or fields.Date.today(), self.company_id.id))
                if self._cr.rowcount > 0:
                    self.rate = 1 / self._cr.fetchone()[0]
                else:
                    self.rate = 0
            else:
               self.rate = 1

    @api.onchange("date_invoice", "currency_id")
    def onchange_date_invoice(self):
        self._get_rate()


    @api.multi
    def update_currency_wizard(self):

        if not self.date_invoice:
            self.date_invoice = fields.Date.today()

        view_id = self.env.ref("ncf_manager.invoice_currency_change_wizard_form", True)
        return {
            'name': _('Cambiar modena de la factura'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.currency.change.wizard',
            'view_id': view_id.id,
            'target': 'new',
            'views': False,
            'type': 'ir.actions.act_window',
            'context': {"currency_id": self.currency_id.id}
        }


    @api.multi
    def update_rate_wizard(self):
        view_id = self.env.ref("currency_rates_control.update_rate_wizard_form", True)
        return {
            'name': _('Fecha sin tasa, Actualizar tasa de la moneda'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.rate.wizard',
            'view_id': view_id.id,
            'target': 'new',
            'views': False,
            'type': 'ir.actions.act_window',
            'context': {"default_name": self.date_invoice or fields.Date.today()}
        }

    overdue_type = fields.Selection(
        [('overlimit_overdue', u'Este cliente tiene el limite de crédito agotado y facturas vencidas'),
         ('overlimit', u'Este cliente no tiene crédito disponible'),
         ('overdue', 'Este cliente tiene facturas vencidas'),
         ('none', 'None'), ], "Estado del credito", compute=_get_overdue_type, copy=False)

    internal_number = fields.Char(u"Número de factura")
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
    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal", required=False,
                              default=_default_user_shop)
    move_name = fields.Char(string='Journal Entry',
                            default=False, copy=False,
                            help="Technical field holding the number given to the invoice, automatically set when the invoice is validated then stored to set the same number again if the invoice is cancelled, set to draft and re-validated.")
    ncf_required = fields.Boolean(copy=True)
    client_fiscal_type = fields.Selection(related="fiscal_position_id.client_fiscal_type")
    supplier_fiscal_type = fields.Selection(related="fiscal_position_id.supplier_fiscal_type")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=_default_user_journal,
                                 domain="[('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale'], 'in_refund': ['purchase'], 'in_invoice': ['purchase']}.get(type, [])), ('company_id', '=', company_id)]")

    purchase_type = fields.Selection([("normal",u"REQUIERE NCF"),
                                      ("minor", u"GASTO MENOR NCF GENERADO POR EL SISTEMA"),
                                      ("informal", u"PROVEEDORES INFORMALES NCF GENERADO POR EL SISTEMA"),
                                      ("exterior", u"PAGOS AL EXTERIOR NO REQUIRE NCF"),
                                      ("import", u"IMPORTACIONES NO REQUIRE NCF"),
                                      ("others", u"OTROS NO REQUIRE NCF"),
                                      ],
                                     string=u"Tipo de compra", default="normal", related="journal_id.purchase_type")
    total_discount = fields.Monetary(string='Descuento', currency_field="company_currency_id",
                                     compute=_get_total_discount)
    credit_out_invoice = fields.Boolean(related="journal_id.credit_out_invoice")
    authorize = fields.Boolean(u"Crédito autorizado", default=False, copy=False)
    move_name = fields.Char(string='Journal Entry', readonly=False,
                            default=False, copy=False,
                            help="Technical field holding the number given to the invoice, automatically set when the invoice is validated then stored to set the same number again if the invoice is cancelled, set to draft and re-validated.")
    rate = fields.Float(u"Tasa del día", compute=_get_rate, digits=(12,4))
    pay_to = fields.Many2one("res.partner", string="Pagar a", readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    charge_to = fields.Many2one("res.partner", string="Facturar a", readonly=True, states={'draft': [('readonly', False)]}, copy=False)

    _sql_constraints = [
        ('number_uniq', 'unique(number, company_id, journal_id, type, partner_id)',
         'Invoice Number must be unique per Company!'),
    ]

    @api.onchange("move_name")
    def onchange_ncf(self):
        if self.move_name and self.type in ('in_invoice','in_refund'):
            if not is_ncf(self.move_name, self.type):
                self.move_name = False
                return {
                    'warning': {'title': "Ncf invalido", 'message': "El numero de comprobante fiscal no es valido "
                                                                    "verifique de que no esta digitando un comprobante"
                                                                    "de consumidor final codigo 02 o revise si lo ha "
                                                                    "digitado incorrectamente"}
                }
            self.invoice_ncf_validation()


    @api.onchange('journal_id')
    def _onchange_journal_id(self):

        if self.journal_id:
            self.currency_id = self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id

        if self.type in ('in_invoice', 'in_refund'):

            if self.purchase_type == "normal":
                self.ncf_required = True
            else:
                self.ncf_required = False

            if not self._context.get("default_supplier", False):

                self.move_name = False

                if not self.partner_id.journal_id:
                    self.partner_id.write({"journal_id": self.journal_id.id})

                if self.purchase_type == "minor":
                    self.partner_id = self.env['res.company']._company_default_get('account.invoice').partner_id.id
                    self.ncf_required = False

                if self.purchase_type != "minor" and self.partner_id.id == self.env.user.company_id.id:
                    self.partner_id = False

            if self.type == "out_invoice" and self.credit_out_invoice == False:
                self.date_due = fields.Date.today()
                self.payment_term_id = 1


    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()
        if self.type in ("in_invoice", "in_refund"):
            self.fiscal_position_id = self.partner_id.property_account_position_supplier_id.id

    @api.onchange("payment_term_id")
    def onchange_payment_term_id(self):
        if self.payment_term_id and self.partner_id.property_payment_term_id.id != self.payment_term_id.id:
            self.env["res.partner"].browse(self.partner_id.id).write(
                {"property_payment_term_id": self.payment_term_id.id})

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):

        if self.fiscal_position_id:

            if self.type in ('out_invoice', 'out_refund'):
                if self.partner_id and self.partner_id.property_account_position_id.id != self.fiscal_position_id.id:
                    self.partner_id.write({"property_account_position_id": self.fiscal_position_id.id})

                shop_user_config = self.env["shop.ncf.config"].get_user_shop_config()

                return {"domain": {
                    "shop_id": [('shop_id', 'in', shop_user_config["shop_ids"])],
                    "journal_id": [('id', 'in', shop_user_config["sale_journal_ids"])]
                }}

            elif self.type in ('in_invoice', 'in_refund'):
                if self.partner_id.journal_id:
                    self.journal_id = self.partner_id.journal_id.id
                elif self.fiscal_position_id.journal_id:
                    self.journal_id = self.fiscal_position_id.journal_id.id

                elif self.journal_id.purchase_type == "normal":
                    self.ncf_required = True
                else:
                    self.ncf_required = False

                if self.partner_id and self.partner_id.property_account_position_supplier_id.id != self.fiscal_position_id.id:
                    self.partner_id.write({"property_account_position_supplier_id": self.fiscal_position_id.id})

    def _check_ncf(self, rnc, ncf):
        if ncf and rnc:
            res = requests.get('http://api.marcos.do/ncf/{}/{}'.format(rnc, ncf))
            if res.status_code == 200:
                return res.json()
        return {}

    @api.multi
    def invoice_ncf_validation(self):
        for invoice in self:
            if not invoice.journal_id.purchase_type in ['exterior', 'import',
                                                        'others'] and invoice.ncf_required == True:

                inv_in_draft = self.search(
                    [('id', '!=', invoice.id), ('partner_id', '=', invoice.partner_id.id),
                     ('move_name', '=', invoice.move_name), ('state', 'in', ('draft', 'cancel'))])

                if inv_in_draft:
                    raise exceptions.ValidationError(
                        u"El número de comprobante fiscal digitado para este proveedor ya se encuentra en una factura en borrador o cancelada.")

                inv_exist = self.search([('partner_id', '=', invoice.partner_id.id), ('number', '=', invoice.move_name),
                                         ('state', 'in', ('open', 'paid'))])
                if inv_exist:
                    raise exceptions.Warning(u"Este número de comprobante ya fue registrado para este proveedor!")

                if _internet_on() and self.journal_id.ncf_remote_validation:
                    result = self._check_ncf(invoice.partner_id.vat, invoice.move_name)
                    if not result.get("valid", False):
                        raise exceptions.UserError("El numero de comprobante fiscal no es valido! "
                                                   "no paso la validacion en DGII, Verifique que el NCF y el RNC del "
                                                   "proveedor esten correctamente digitados, si es de proveedor informal o de "
                                                   "gasto menor vefifique si debe solicitar nuevos numero.")

            self.signal_workflow("invoice_open")

    @api.model
    def create(self, vals):
        if not vals.get("partner_id", False):
            vals.update({"partner_id": self.env.user.company_id.partner_id.id})
        res = super(AccountInvoice, self).create(vals)
        return res


    @api.multi
    def write(self, vals):
        for rec in self:
            if rec.type in ("out_invoice", "out_refund"):
                if not vals.get("fiscal_position_id", False):
                    if not rec.fiscal_position_id:
                        fiscal_position_id = rec.env["account.fiscal.position"].search([('client_fiscal_type', '=', 'final')])
                        if not fiscal_position_id:
                            raise exceptions.ValidationError(
                                "Antes de generar una factura debe definir las posiciones fiscales.")
                        else:
                            vals.update({"fiscal_position_id": fiscal_position_id.id})

            if rec.type in ("in_invoice", "in_refund"):
                if vals.get("purchase_type", False) == "minor":
                    vals.update({"partner_id": self.env.user.company_id.partner_id.id})

        return super(AccountInvoice, self).write(vals)

    @api.model
    def _refund_cleanup_lines(self, lines):
        """ Convert records to dict of values suitable for one2many line creation

            :param recordset lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """

        if not lines:
            return []

        refund_type = self._context.get("refund_type", False)

        days = 0
        if lines:
            days = self.get_days_between(lines[0].invoice_id.date_invoice)

        result = []
        for line in lines:
            values = {}
            for name, field in line._fields.iteritems():
                if name in MAGIC_COLUMNS:
                    continue
                elif field.type == 'many2one':
                    values[name] = line[name].id
                elif field.type not in ['many2many', 'one2many']:
                    if name == "quantity":
                        if not refund_type:
                            values[name] = line.qty_allow_refund
                        else:
                            values["quantity"] = line[name]
                    elif name == "qty_allow_refund":
                        if not refund_type:
                            values[name] = line.qty_allow_refund
                        else:
                            values["qty_allow_refund"] = line["quantity"]
                    else:
                        values[name] = line[name]
                elif name == 'invoice_line_tax_ids':
                    if days > 30:
                        continue
                    values[name] = [(6, 0, line[name].ids)]

                values["refund_line_ref"] = line.id

            if not values:
                return []
            if lines._model == "account.invoice.line":
                if values.get("quantity", False) == 0.00:
                    continue
            result.append((0, 0, values))

        if not result:
            raise exceptions.UserError("Todos los productos de esta factura ya fueron devueltos.")

        return result

    @api.multi
    def invoice_validate(self):
        for rec in self:
            if rec.type in ["out_invoice", "in_invoice"]:
                for line in rec.invoice_line_ids:
                    line.qty_allow_refund = line.quantity
            elif rec.type in ["out_refund", "in_refund"]:
                for line in rec.invoice_line_ids:
                    if line.product_id:
                        if line.quantity > line.qty_allow_refund:
                            pass
                            # raise exceptions.UserError("No puede devolver mas productos de que los facturados.")

                    origin = self.env["account.invoice.line"].browse(line.refund_line_ref.id)
                    origin.write({"qty_allow_refund": origin.qty_allow_refund - line.quantity})

                refund_inv = self.env['account.invoice'].search([('origin', '=', rec.number), ('state', 'in', ('open', 'paid'))])

                total_refund = sum([rec.amount_untaxed for rec in refund_inv]) + rec.amount_untaxed

                afected_inv = self.env['account.invoice'].search([('number', '=', rec.origin), ('state', 'in', ('open', 'paid'))])

                amount_untaxed = sum([r.amount_untaxed for r in afected_inv]) or 0.0

                # if total_refund > amount_untaxed:
                #     raise exceptions.UserError(u"No puede crear notas de credito por un valor mayor a la factura afectada.")

        res = super(AccountInvoice, self).invoice_validate()
        return res

    def get_days_between(self, joining_date):

        date_format = '%Y-%m-%d'
        current_date = datetime.strptime(datetime.today().strftime(date_format), date_format)
        doc_date = datetime.strptime(joining_date, date_format)
        delta = current_date - doc_date
        return delta.days

    @api.one
    def _get_outstanding_info_JSON(self):
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.state == 'open':
            domain = [('journal_id.type', 'in', ('bank', 'cash', 'sale')), ('account_id', '=', self.account_id.id),
                      ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                      ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
            if self.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')
            info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
            lines = self.env['account.move.line'].search(domain)
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    # get the outstanding residual value in its currency. We don't want to show it
                    # in the invoice currency since the exchange rate between the invoice date and
                    # the payment date might have changed.
                    if line.currency_id:
                        currency_id = line.currency_id
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        currency_id = line.company_id.currency_id
                        amount_to_show = abs(line.amount_residual)
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, self.currency_id.decimal_places],
                    })
                info['title'] = type_payment
                self.outstanding_credits_debits_widget = json.dumps(info)
                self.has_outstanding = True

    @api.one
    def copy(self, default=None):
        if self.type in ("in_refund", "out_refund"):
            raise exceptions.UserError("No esta permitido duplicar notas de crédito!")
        return super(AccountInvoice, self).copy(default=default)

    @api.multi
    def authorize_credit(self):
        for rec in self:
            overdue_type = {'overlimit_overdue': u'Este cliente, tiene el limite de crédito agotado y facturas vencidas',
                            'overlimit': u'Este cliente, no tiene crédito disponible',
                            'overdue': 'Este cliente, tiene facturas vencidas',
                            'none': 'None'}
            rec.authorize = True
            rec.message_post(body=u"<p>Crédito autorizado con {}</p>".format(overdue_type[rec.overdue_type]),
                              subject=u"factura a Crédito Autorizada", subtype="mail.mt_comment")

    @api.multi
    def disallows_credit(self):
        for rec in self:
            overdue_type = {'overlimit_overdue': u'Este cliente, tiene el limite de crédito agotado y facturas vencidas',
                            'overlimit': u'Este cliente, no tiene crédito disponible',
                            'overdue': 'Este cliente, tiene facturas vencidas',
                            'none': 'None'}
            rec.authorize = False
            rec.message_post(body=u"<p>Crédito cancelado con {}</p>".format(overdue_type[rec.overdue_type]),
                              subject=u"factura a Crédito no autorizada", subtype="mail.mt_comment")


    @api.multi
    def set_ncf(self):
        for inv in self:
            if inv.type == 'out_invoice' and not inv.move_name and inv.journal_id.ncf_control:
                fiscal_type = inv.fiscal_position_id.client_fiscal_type
                if fiscal_type == 'fiscal':
                    sequence = inv.journal_id.fiscal_sequence_id
                elif fiscal_type == 'gov':
                    sequence = inv.journal_id.gov_sequence_id
                elif fiscal_type == 'special':
                    sequence = inv.journal_id.special_sequence_id
                elif fiscal_type == 'unico':
                    sequence = inv.journal_id.unique_sequence_id
                else:
                    sequence = inv.journal_id.final_sequence_id

                if not sequence:
                    raise exceptions.ValidationError("Las secuencias para este diario de ventas no estan configuradas.")

                next_ncf = True
                while next_ncf:
                    ncf_next = sequence.with_context(ir_sequence_date=inv.date_invoice).next_by_id()
                    if not self.search_count([('number','=',ncf_next),('journal_id','=',self.journal_id.id)]):
                        _logger.info(
                            "EL SISTEMA SALTO EL NUMERO {} DEL DIARIO {} PORQUE YA EXISTE DESDE CONTABILIDAD".format(
                                ncf_next, self.journal_id.name))
                        next_ncf = False

                inv.move_name = ncf_next


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.one
    def compute_tax_line(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
            self.tax_amount = sum([t["amount"] for t in taxes["taxes"]])
        else:
            self.tax_amount = 0.0

    qty_allow_refund = fields.Float(string='qty allow refund', digits=dp.get_precision('Product Unit of Measure'),
                                    required=False, copy=False)
    refund_line_ref = fields.Many2one("account.invoice.line", string="origin line refund", copy=False)
    tax_amount = fields.Monetary(string='tax_amount', required=False, currency_field="company_currency_id",
                                 compute=compute_tax_line)
