# -*- coding: utf-8 -*-
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
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf
except(ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @api.depends('currency_id', "date_invoice")
    def _get_rate(self):
        for inv in self:
            if not inv.is_company_currency:
                try:
                    rate = inv.currency_id.with_context(
                        dict(self._context or {}, date=inv.date_invoice))
                    inv.invoice_rate = 1 / rate.rate
                    inv.rate_id = rate.res_currency_rate_id
                except(Exception) as err:
                    _logger.debug(err)

    @api.multi
    @api.depends("currency_id")
    def _is_company_currency(self):
        for inv in self:
            if inv.currency_id == inv.company_id.currency_id:
                inv.is_company_currency = True
            else:
                inv.is_company_currency = False

    # deprecate on odoo 11
    # def _default_user_shop(self):
    #     Shop = self.env["shop.ncf.config"]
    #     shop_user_config = False
    #
    #     if not self.journal_id:
    #         shop_user_config = Shop.sudo().search(
    #             [('user_ids', 'in', self._uid)])
    #     else:
    #         shop_user_config = Shop.sudo().search([
    #             ('user_ids', 'in', self._uid),
    #             ('journal_id', '=', self.journal_id.id)])
    #
    #     if shop_user_config:
    #         return shop_user_config[0]
    #     else:
    #         return False

    shop_id = fields.Many2one("shop.ncf.config", string="Sucursal")
    # deprecate on odoo 11
    # required=False,
    # default=_default_user_shop,
    # domain=lambda s: [('user_ids', '=', [s._uid])])

    ncf_control = fields.Boolean(related="journal_id.ncf_control")
    purchase_type = fields.Selection(related="journal_id.purchase_type")

    sale_fiscal_type = fields.Selection([("final", "Consumidor Final"),
                                         ("fiscal", u"Crédito Fiscal"),
                                         ("gov", "Gubernamental"),
                                         ("special", u"Regímenes Especiales"),
                                         ("unico", u"Único Ingreso")])

    income_type = fields.Selection(
        [('01', '01 - Ingresos por operaciones (No financieros)'),
         ('02', '02 - Ingresos Financieros'),
         ('03', '03 - Ingresos Extraordinarios'),
         ('04', '04 - Ingresos por Arrendamientos'),
         ('05', '05 - Ingresos por Venta de Activo Depreciable'),
         ('06', '06 - Otros Ingresos')],
        string="Tipo de Ingreso")

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
         ('11', '11 - Gastos de Seguros')],
        string="Tipo de Costos y Gastos")

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
    origin_out = fields.Char("Afecta a", related="origin")
    internal_sequence = fields.Char(string=u"Número de factura")

    _sql_constraints = [
        ('number_uniq',
         'unique(number, company_id, partner_id, journal_id, type)',
         'Invoice Number must be unique per Company!'),
    ]

    def purchase_ncf_validate(self):
        if not self.journal_id.purchase_type == 'normal':
            return

        number = self.move_name if self.move_name else None

        if not ncf.is_valid(number):
            raise UserError(_(
                "NCF mal digitado\n\n"
                "El comprobante *{}* no tiene la estructura correcta "
                "valide si lo ha digitado correctamente".format(number)))

        if number[9:11] not in (
                '01', '03', '04', '11', '12', '13', '14', '15'):
            raise ValidationError(_(
                "NCF *{}* NO corresponde con el tipo de documento\n\n"
                "Verifique lo ha digitado correctamente y que no sea un "
                "Comprobante Consumidor Final (02)".format(number)))

        if self.id:
            ncf_in_draft = self.search_count(
                [('id', '!=', self.id),
                 ('partner_id', '=', self.partner_id.id),
                 ('move_name', '=', number),
                 ('state', 'in', ('draft', 'cancel'))])

        else:
            ncf_in_draft = self.search_count(
                [('partner_id', '=', self.partner_id.id),
                 ('move_name', '=', number),
                 ('state', 'in', ('draft', 'cancel'))])

        if ncf_in_draft:
            raise UserError(_(
                "NCF en Factura Borrador o Cancelada\n\n"
                "El comprobante *{}* ya se encuentra "
                "registrado con este mismo proveedor en una factura "
                "en borrador o cancelada".format(number)))

        ncf_exist = self.search_count(
            [('partner_id', '=', self.partner_id.id),
             ('number', '=', number),
             ('state', 'in', ('open', 'paid'))])
        if ncf_exist:
            raise UserError(_(
                "NCF Duplicado\n\n"
                "El comprobante *{}* ya se encuentra registrado con el"
                " mismo proveedor en otra factura".format(number)))

        if self.journal_id.ncf_remote_validation and not ncf.check_dgii(self.partner_id.vat, number):
            raise UserError(_(
                u"NCF NO pasó validación en DGII\n\n"
                u"¡El número de comprobante *{}* del proveedor "
                u"*{}* no pasó la validación en "
                "DGII! Verifique que el NCF y el RNC del "
                u"proveedor estén correctamente "
                u"digitados, o si los números de ese NCF se "
                "le agotaron al proveedor".format(number,
                                                  self.partner_id.name)
            ))

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        super(AccountInvoice, self)._onchange_journal_id()
        if self.journal_id.type == 'purchase' \
            and self.journal_id.purchase_type == "minor":
            self.partner_id = self.company_id.partner_id.id

    @api.onchange('journal_id', 'partner_id')
    def onchange_journal_id(self):
        if self.journal_id.type == 'purchase' \
            and self.journal_id.purchase_type == "minor":
            self.partner_id = self.company_id.partner_id.id

        if self.partner_id.id == self.company_id.partner_id.id:
            journal_id = self.env['account.journal'].search([
                ('purchase_type', '=', 'minor')])
            if not journal_id:
                raise ValidationError(
                    _("No existe un Diario de Gastos Menores,"
                      " debe crear uno."))
            self.journal_id = journal_id.id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id and self.type == 'out_invoice':
            if self.journal_id.ncf_control:
                self.sale_fiscal_type = self.partner_id.sale_fiscal_type
                self.special_check()
            if not self.partner_id.customer:
                self.partner_id.customer = True
        elif self.partner_id and self.type == 'in_invoice':
            self.expense_type = self.partner_id.expense_type
            if not self.partner_id.supplier:
                self.partner_id.supplier = True

        return res

    @api.onchange('sale_fiscal_type', 'expense_type')
    def _onchange_fiscal_type(self):
        if self.partner_id:
            if self.type == 'out_invoice' and self.journal_id.ncf_control:
                self.partner_id.write(
                    {'sale_fiscal_type': self.sale_fiscal_type})
                self.special_check()

            if self.type == 'in_invoice':
                self.partner_id.write({'expense_type': self.expense_type})

    def special_check(self):
        if self.sale_fiscal_type == "special":
            self.fiscal_position_id = self.journal_id.special_fiscal_position_id
        else:
            self.fiscal_position_id = False

    # deprecate
    # @api.onchange("shop_id")
    # def onchange_shop_id(self):
    #     if self.type in ('out_invoice', 'out_refund'):
    #         self.journal_id = self.shop_id.journal_id.id

    @api.onchange("move_name")
    def onchange_ncf(self):
        if self.type in ("in_invoice", "in_refund") and self.move_name:
            self.purchase_ncf_validate()

    @api.multi
    def action_invoice_open(self):
        for inv in self:
            sequence_obj = self.env['ir.sequence']

            if inv.journal_id.ncf_control and not inv.partner_id.sale_fiscal_type:
                raise ValidationError(_(
                    u"El cliente [{}]{} no tiene Tipo de comprobante, y es requerido"
                    "para este tipo de factura.".format(inv.partner_id.id,
                                                        inv.partner_id.name)))

            if inv.type == "out_invoice" and inv.sale_fiscal_type in (
                    "fiscal", "gov", "special") and inv.journal_id.ncf_control and not inv.partner_id.vat:
                raise UserError(_(
                    u"El cliente [{}]{} no tiene RNC/Cédula, y es requerido"
                    "para este tipo de factura.".format(inv.partner_id.id,
                                                        inv.partner_id.name)))
            elif inv.type in ("in_invoice", "in_refund"):
                if inv.journal_id.purchase_type in ('normal', 'informal') and not inv.partner_id.vat:
                    raise UserError(_(
                        u"¡Para este tipo de Compra el Proveedor"
                        u" debe de tener un RNC/Cédula establecido!"))
                self.purchase_ncf_validate()

            if inv.type == "out_invoice":
                inv.internal_sequence = sequence_obj.next_by_code(
                'client.invoice.number')
            else:
                inv.internal_sequence = sequence_obj.next_by_code(
                'supplier.invoice.number')

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
