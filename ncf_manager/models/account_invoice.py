# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>

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
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf
except(ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def is_ncf(value, inv):
        """
        Valida estructura del Número de Comprobante Fiscal (NCF)
        para República Dominicana.

        :param value: string con NCF

        :returns: True when the structure is OK, False if is not; according
         to the type of invoice.
        """
        if not value:
            return False

        if ncf.is_valid(value):
            if (type in ("in_refund", "out_refund") and value[9:11] in ('03',
                                                                        '04')
                or type == "in_invoice" and value[9:11] in ('01', '03', '11',
                                                            '12', '13', '14',
                                                            '15')
                or type == "out_invoice" and value[9:11] in ('01', '02', '03',
                                                             '12', '14',
                                                             '15')):
                return True

            return False

    @api.multi
    @api.depends('currency_id', "date_invoice")
    def _get_rate(self):
        for rec in self:
            if not rec.is_company_currency:
                try:
                    rate = rec.currency_id.with_context(
                        dict(self._context or {}, date=rec.date_invoice))
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
        Shop = self.env["shop.ncf.config"]
        shop_user_config = False

        if not self.journal_id:
            shop_user_config = Shop.sudo().search(
                [('user_ids', 'in', self._uid)])
        else:
            shop_user_config = Shop.sudo().search([
                ('user_ids', 'in', self._uid),
                ('journal_id', '=', self.journal_id.id)])

        if shop_user_config:
            return shop_user_config[0]
        else:
            return False

    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal",
                              required=False,
                              default=_default_user_shop,
                              domain=lambda s: [('user_ids', '=', [s._uid])])

    ncf_control = fields.Boolean(related="journal_id.ncf_control")
    purchase_type = fields.Selection(related="journal_id.purchase_type")

    sale_fiscal_type = fields.Selection(
        [("final", "Consumidor Final"),
         ("fiscal", u"Crédito Fiscal"),
         ("gov", "Gubernamental"),
         ("special", u"Regímenes Especiales"),
         ("unico", u"Único ingreso")],
        string="NCF para")

    expense_type = fields.Selection(
        [('01', '01 - Gastos de Personal'),
         ('02', '02 - Gastos por Trabajo, Suministros y Servicios'),
         ('03', '03 - Arrendamientos'),
         ('04', '04 - Gastos de Activos Fijos'),
         ('05', u'05 - Gastos de Representación'),
         ('06', '06 - Otras Deducciones Admitidas'),
         ('07', '07 - Gastos Financieros'),
         ('08', '08 - Gastos Extraordinarios'),
         ('09', '09 - Compras y Gastos que forman parte del Costo de Venta'),
         ('10', '10 - Adquisiciones de Activos'),
         ('11', '11 - Gastos de Seguro')],
        string="Tipo de gasto")

    anulation_type = fields.Selection(
        [("01", "01 - Deterioro de Factura Pre-impresa"),
         ("02", u"02 - Errores de Impresión (Factura Pre-impresa)"),
         ("03", u"03 - Impresión Defectuosa"),
         ("04", "04 - Duplicidad de Factura"),
         ("05", u"05 - Corrección de La Información"),
         ("06", "06 - Cambio de Productos"),
         ("07", u"07 - Devolución de Productos"),
         ("08", u"08 - Omisión de Productos"),
         ("09", "09 - Errores en Secuencia de NCF")],
        string=u"Tipo de anulación", copy=False)

    is_company_currency = fields.Boolean(compute=_is_company_currency)

    invoice_rate = fields.Monetary(string="Tasa", compute=_get_rate,
                                   currency_field='currency_id')
    purchase_type = fields.Selection(
        [("normal", "Requiere NCF"),
         ("minor", "Gasto Menor. NCF Generado por el Sistema"),
         ("informal", "Proveedores Informales. NCF Generado por el Sistema"),
         ("exterior", "Pagos al Exterior. NCF Generado por el Sistema"),
         ("import", "Importaciones. NCF Generado por el Sistema"),
         ("others", "Otros. No requiere NCF")],
        string="Tipo de Compra",
        related="journal_id.purchase_type")

    is_nd = fields.Boolean()
    origin_out = fields.Char(u"Afecta a", related="origin")

    _sql_constraints = [
        ('number_uniq',
         'unique(number, company_id, partner_id, journal_id, type)',
         'Invoice Number must be unique per Company!'),
    ]

    def invoice_ncf_validation(self):
        if not self.journal_id.ncf_remote_validation:
            return True

        if not self.is_ncf(self.move_name, self.type):
            raise UserError(_(
                u"NCF Mal Digitado o Inválido\n\n"
                u"El comprobante *{}* no es válido. Verifique "
                "si lo ha digitado correctamente y que no sea un "
                "Comprobante Consumidor Final (02)".format(self.move_name))
            )

        elif self.journal_id.purchase_type not in ['exterior', 'import',
                                                   'others'] and self.journal_id.type == "purchase":

            if self.id:
                inv_in_draft = self.search_count(
                    [('id', '!=', self.id),
                     ('partner_id', '=', self.partner_id.id),
                     ('move_name', '=', self.move_name),
                     ('state', 'in', ('draft', 'cancel'))])
            else:
                inv_in_draft = self.search_count(
                    [('partner_id', '=', self.partner_id.id),
                     ('move_name', '=', self.move_name),
                     ('state', 'in', ('draft', 'cancel'))])

            if inv_in_draft:
                raise UserError(_(
                    "NCF Duplicado\n\n"
                    "El comprobante *{}* ya se encuentra "
                    "registrado con este mismo proveedor en una factura "
                    "en borrador o cancelada".format(self.move_name)))

            inv_exist = self.search_count(
                [('partner_id', '=', self.partner_id.id),
                 ('number', '=', self.move_name),
                 ('state', 'in', ('open', 'paid'))])
            if inv_exist:
                raise UserError(_(
                    "NCF Duplicado\n\n"
                    "El comprobante *{}* ya se encuentra registrado con el "
                    "mismo proveedor en otra factura".format(
                        self.move_name)))

            if self.journal_id.ncf_remote_validation:
                is_valid = ncf.check_dgii(self.partner_id.vat, self.move_name)
                if not is_valid:
                    raise UserError(_(
                        u"NCF NO pasó validación en DGII\n\n"
                        u"¡El número de comprobante *{}* del proveedor "
                        u"*{}* no pasó la validación en "
                        "DGII! Verifique que el NCF y el RNC del "
                        u"proveedor estén correctamente "
                        u"digitados, o si los números de ese NCF se "
                        "le agotaron al proveedor".format(
                            self.move_name,
                            self.partner_id.name)))
        return True

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        super(AccountInvoice, self)._onchange_journal_id()
        if self.journal_id.type == 'purchase' and self.journal_id.purchase_type == "minor":
            self.partner_id = self.company_id.partner_id.id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id and self.type == 'out_invoice':
            if self.journal_id.ncf_control:
                self.sale_fiscal_type = self.partner_id.sale_fiscal_type
            if not self.partner_id.customer:
                self.partner_id.customer = True
        elif self.partner_id and self.type == 'in_invoice':
            self.expense_type = self.partner_id.expense_type
            if not self.partner_id.supplier:
                self.partner_id.supplier = True

        if self.journal_id.purchase_type == "minor":
            self.partner_id = self.company_id.partner_id.id

    @api.onchange('sale_fiscal_type', 'expense_type')
    def _onchange_fiscal_type(self):
        if self.partner_id:
            if self.type == 'out_invoice':
                self.partner_id.write(
                    {'sale_fiscal_type': self.sale_fiscal_type})

                if self.sale_fiscal_type == "special":
                    pass
                    # self.fiscal_position_id = self.env.ref(
                    #     "ncf_manager.ncf_manager_special_fiscal_position")

            if self.type == 'in_invoice':
                self.partner_id.write({'expense_type': self.expense_type})

    @api.onchange("shop_id")
    def onchange_shop_id(self):
        if self.type in ('out_invoice', 'out_refund'):
            self.journal_id = self.shop_id.journal_id.id

    @api.onchange("move_name")
    def onchange_ncf(self):
        if self.type in ("in_invoice", "in_refund") and self.move_name:
            self.invoice_ncf_validation()

    @api.multi
    def action_invoice_open(self):
        for rec in self:
            if rec.journal_id.ncf_control and not rec.partner_id.sale_fiscal_type:
                rec.sale_fiscal_type = "final"
            if rec.type == "out_invoice" and rec.sale_fiscal_type in ("fiscal", "gov", "special") and rec.journal_id.ncf_control and not rec.partner_id.vat:
                raise UserError(_(
                    u"El cliente [{}]{} no tiene RNC/Cédula, y es requerido"
                    "para este tipo de factura.".format(rec.partner_id.id,
                                                        rec.partner_id.name)))

            elif rec.type in ("in_invoice", "in_refund"):
                if rec.journal_id.purchase_type in ('normal', 'informal') and not rec.partner_id.vat:
                    raise UserError(_(
                        u"¡Para este tipo de Compra el Proveedor"
                        u" debe de tener un RNC/Cédula establecido!"))
                self.invoice_ncf_validation()

        return super(AccountInvoice, self).action_invoice_open()

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)

        if self._context.get("credit_note_supplier_ncf", False):
            res.update({"move_name": self._context["credit_note_supplier_ncf"]
                        })
        return res
