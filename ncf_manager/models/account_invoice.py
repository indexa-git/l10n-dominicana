# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Yasmany Castillo <yasmany003@gmail.com>
# © 2018 José López <jlopez@indexa.do>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
# © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
# © 2018 Andrés Rodríguez <andres@iterativo.do>

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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf as ncf_validation, rnc, cedula
except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    reference = fields.Char(string='NCF')

    sequence_almost_depleted = fields.Boolean(
        compute="_compute_sequence_almost_depleted")

    @api.depends('journal_id', 'sale_fiscal_type')
    def _compute_sequence_almost_depleted(self):
        for invoice in self:
            if invoice.journal_id.ncf_control and invoice.type == "out_invoice" and \
               invoice.sale_fiscal_type:
                sequence = invoice.journal_id.date_range_ids.filtered(
                    lambda seq: seq.sale_fiscal_type == invoice.
                    sale_fiscal_type)
                if sequence:
                    if sequence.number_next_actual >= sequence.warning_ncf:
                        invoice.sequence_almost_depleted = True
                    else:
                        invoice.sequence_almost_depleted = False

            if invoice.journal_id.purchase_type in (
                    'informal', 'minor',
                    'exterior') and invoice.type == "in_invoice" and \
                    invoice.journal_id.purchase_type:
                sequence = invoice.journal_id.date_range_ids.filtered(
                    lambda seq: seq.sale_fiscal_type == invoice.journal_id.
                    purchase_type)
                if sequence:
                    if sequence.number_next_actual >= sequence.warning_ncf:
                        invoice.sequence_almost_depleted = True
                    else:
                        invoice.sequence_almost_depleted = False

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
                except (Exception) as err:
                    _logger.debug(err)

    @api.multi
    @api.depends("currency_id")
    def _is_company_currency(self):
        for inv in self:
            if inv.currency_id == inv.company_id.currency_id:
                inv.is_company_currency = True
            else:
                inv.is_company_currency = False

    @api.multi
    @api.depends('state')
    def _compute_ncf_expiration_date(self):
        for inv in self:
            if inv.state != 'draft' and inv.journal_id.ncf_control:
                if inv.sale_fiscal_type:
                    try:
                        inv.ncf_expiration_date = [
                            dr.date_to
                            for dr in inv.journal_id.date_range_ids
                            if dr.sale_fiscal_type == inv.sale_fiscal_type][0]
                    except IndexError:
                        raise ValidationError(
                            _('Error. No sequence range for NCF para: {}')
                            .format(inv.sale_fiscal_type))

    ncf_control = fields.Boolean(related="journal_id.ncf_control")
    purchase_type = fields.Selection(related="journal_id.purchase_type")

    sale_fiscal_type = fields.Selection([
        ("final", "Consumo"),
        ("fiscal", u"Crédito Fiscal"),
        ("gov", "Gubernamentales"),
        ("special", u"Regímenes Especiales"),
        ("unico", u"Único Ingreso"),
        ("export", u"Exportaciones"),
    ],
        string='NCF para',
        default=lambda self: self._context.get('sale_fiscal_type', 'final'))

    income_type = fields.Selection(
        [('01', '01 - Ingresos por Operaciones (No Financieros)'),
         ('02', '02 - Ingresos Financieros'),
         ('03', '03 - Ingresos Extraordinarios'),
         ('04', '04 - Ingresos por Arrendamientos'),
         ('05', '05 - Ingresos por Venta de Activo Depreciable'),
         ('06', '06 - Otros Ingresos')],
        string='Tipo de Ingreso',
        default=lambda self: self._context.get('income_type', '01'))

    expense_type = fields.Selection(
        [('01', '01 - Gastos de Personal'),
         ('02', '02 - Gastos por Trabajo, Suministros y Servicios'),
         ('03', '03 - Arrendamientos'), ('04', '04 - Gastos de Activos Fijos'),
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
         ("04", u"04 - Corrección de la Información"),
         ("05", "05 - Cambio de Productos"),
         ("06", u"06 - Devolución de Productos"),
         ("07", u"07 - Omisión de Productos"),
         ("08", "08 - Errores en Secuencia de NCF"),
         ("09", "09 - Por Cese de Operaciones"),
         ("10", u"10 - Pérdida o Hurto de Talonarios")],
        string=u"Tipo de anulación",
        copy=False)

    is_company_currency = fields.Boolean(compute=_is_company_currency)

    invoice_rate = fields.Monetary(string="Tasa",
                                   compute=_get_rate,
                                   currency_field='currency_id')

    is_nd = fields.Boolean("Es Nota de Débito")
    origin_out = fields.Char("Afecta a")
    ncf_expiration_date = fields.Date('Válido hasta',
                                      compute="_compute_ncf_expiration_date",
                                      store=True)

    @api.multi
    @api.constrains('state', 'tax_line_ids')
    def validate_special_exempt(self):
        """ Validates an invoice with Regímenes Especiales sale_fiscal_type
            does not contain nor ITBIS or ISC.

            See DGII Norma 05-19, Art 3 for further information.
        """
        for inv in self:
            if inv.type == 'out_invoice' and inv.state in (
                    'open', 'cancel') and inv.sale_fiscal_type == 'special':

                # If any invoice tax in ITBIS or ISC
                if any([
                        tax for tax in inv.tax_line_ids.mapped('tax_id')
                        .filtered(lambda tax: tax.tax_group_id.name in (
                            'ITBIS', 'ISC') and tax.amount != 0)
                ]):
                    raise UserError(_(
                        "No puede validar una factura para Regímen Especial "
                        " con ITBIS/ISC.\n\n"
                        "Consulte Norma General 05-19, Art. 3 de la DGII")
                    )

    def validate_fiscal_purchase(self):
        NCF = self.reference if self.reference else None
        if NCF and self.journal_id.purchase_type == 'normal':
            if NCF[-10:-8] == '02' or NCF[1:3] == '32':
                raise ValidationError(_(
                    "NCF *{}* NO corresponde con el tipo de documento\n\n"
                    "No puede registrar Comprobantes Consumidor Final (02)")
                    .format(NCF))

            elif not ncf_validation.is_valid(NCF):
                raise UserError(_(
                    "NCF mal digitado\n\n"
                    "El comprobante *{}* no tiene la estructura correcta "
                    "valide si lo ha digitado correctamente")
                    .format(NCF))

            elif not self.partner_id.vat:
                raise ValidationError(_(
                    u"Proveedor sin RNC/Céd\n\n"
                    u"El proveedor *{}* no tiene RNC o Cédula y es requerido "
                    u"para registrar compras Fiscales")
                    .format(self.partner_id.name))

            elif (self.journal_id.ncf_remote_validation and len(NCF) == 11 and
                  not ncf_validation.check_dgii(self.partner_id.vat, NCF)):
                raise ValidationError(_(
                    u"NCF NO pasó validación en DGII\n\n"
                    u"¡El número de comprobante *{}* del proveedor "
                    u"*{}* no pasó la validación en "
                    "DGII! Verifique que el NCF y el RNC del "
                    u"proveedor estén correctamente "
                    u"digitados, o si los números de ese NCF se "
                    "le agotaron al proveedor")
                    .format(NCF, self.partner_id.name))

            ncf_in_invoice = self.search_count([
                ('id', '!=', self.id), ('company_id', '=', self.company_id.id),
                ('partner_id', '=', self.partner_id.id),
                ('reference', '=', NCF),
                ('state', 'in', ('draft', 'open', 'paid', 'cancel')),
                ('type', 'in', ('in_invoice', 'in_refund'))
            ]) if self.id else self.search_count(
                [('partner_id', '=', self.partner_id.id),
                 ('company_id', '=', self.company_id.id),
                 ('reference', '=', NCF),
                 ('state', 'in', ('draft', 'open', 'paid', 'cancel')),
                 ('type', 'in', ('in_invoice', 'in_refund'))])

            if ncf_in_invoice:
                raise ValidationError(_(
                    "NCF Duplicado en otra Factura\n\n"
                    "El comprobante *{}* ya se encuentra "
                    "registrado con este mismo proveedor en una factura "
                    "en borrador o cancelada").format(NCF))

    @api.onchange('journal_id', 'partner_id')
    def onchange_journal_id(self):
        res = super(AccountInvoice, self)._onchange_journal_id()
        if self.journal_id.type == 'purchase':
            if self.journal_id.purchase_type == "minor":
                self.partner_id = self.company_id.partner_id.id

            if self.partner_id.id == self.company_id.partner_id.id:
                journal_id = self.env['account.journal'].search([
                    ('purchase_type', '=', 'minor'),
                    ('company_id', '=', self.company_id.id)
                ])
                if not journal_id:
                    raise ValidationError(
                        _("No existe un Diario de Gastos Menores,"
                          " debe crear uno."))
                self.journal_id = journal_id.id
        return res

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id and self.type == 'out_invoice':
            if self.journal_id.ncf_control:
                self.sale_fiscal_type = self.partner_id.sale_fiscal_type
                self.special_check()
            if not self.partner_id.customer:
                self.partner_id.customer = True
        elif self.partner_id and self.type == 'in_invoice' and not self.expense_type:
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

            if self.type == 'in_invoice' and not self.partner_id.expense_type:
                self.partner_id.write({'expense_type': self.expense_type})

    def special_check(self):
        if self.sale_fiscal_type == "special":
            self.fiscal_position_id = \
                self.journal_id.special_fiscal_position_id
        else:
            self.fiscal_position_id = False

    @api.onchange("reference", "origin_out")
    def onchange_ncf(self):
        if self.journal_id.purchase_type in ('normal', 'informal', 'minor'):
            self.validate_fiscal_purchase()

        if self.origin_out and (self.type == 'out_refund' or
                                self.type == 'in_refund'):
            if self.journal_id.purchase_type in (
                    'normal', 'informal',
                    'minor') or self.journal_id.ncf_control:
                ncf = self.origin_out
                if not ncf_validation.is_valid(ncf) and (
                   ncf[-10:-8] != '04' or ncf[1:3] != '34'):
                    raise UserError(_(
                        "NCF mal digitado\n\n"
                        "El comprobante *{}* no tiene la estructura correcta "
                        "valide si lo ha digitado correctamente").format(ncf))

    @api.multi
    @api.constrains('state', 'invoice_line_ids', 'partner_id')
    def validate_products_export_ncf(self):
        """ Validates that an invoices with a partner from country != DO
            and products type != service must have Exportaciones NCF.

            See DGII Norma 05-19, Art 10 for further information.
        """
        for inv in self:
            if (inv.type == 'out_invoice' and
                    inv.state in ('open', 'cancel') and
                    inv.partner_id.country_id and
                    inv.partner_id.country_id.code != 'DO' and
                    inv.journal_id.ncf_control):
                if any([
                        p for p in inv.invoice_line_ids.mapped('product_id')
                        if p.type != 'service'
                ]):
                    if inv.sale_fiscal_type != 'export':
                        raise UserError(_(
                            "La venta de bienes a clientes extranjeros deben "
                            "realizarse con comprobante tipo Exportaciones"))
                else:
                    if inv.sale_fiscal_type != 'final':
                        raise UserError(_(
                            "La venta de servicios a clientes extranjeros "
                            "deben realizarse con comprobante tipo Consumo"))

    @api.constrains('state', 'tax_line_ids')
    def validate_informal_withholding(self):
        """ Validates an invoice with Comprobante de Compras has 100% ITBIS
            withholding.

            See DGII Norma 05-19, Art 7 for further information.
        """

        for inv in self:
            if (inv.type == 'in_invoice' and inv.state == 'open' and
                    inv.journal_id.purchase_type == 'informal'):

                # If the sum of all taxes of category ITBIS is not 0
                if sum([
                        tax.amount for tax in inv.tax_line_ids.mapped('tax_id')
                        .filtered(lambda t: t.tax_group_id.name == 'ITBIS')
                ]):
                    raise UserError(_("Debe retener el 100% del ITBIS"))

    @api.multi
    def action_invoice_open(self):
        for inv in self:
            if inv.amount_total == 0:
                raise UserError(_(
                    u"No se puede validar una factura cuyo monto total sea"
                    " igual a 0."))

            if inv.type == "out_invoice" and inv.journal_id.ncf_control:
                if not inv.partner_id.sale_fiscal_type:
                    raise ValidationError(_(
                        u"El cliente [{}]{} no tiene Tipo de comprobante, y es"
                        "requerido para este tipo de factura.").format(
                            inv.partner_id.id, inv.partner_id.name))

                sequence = inv.journal_id.date_range_ids.filtered(
                    lambda seq: seq.sale_fiscal_type == inv.sale_fiscal_type)
                if sequence.number_next_actual > sequence.max_number_next:
                    raise ValidationError(_(
                        u"Los comprobantes para {} se han agotado,"
                        " contacte al responsable de contabilidad ({}).").format(
                        dict(self._fields['sale_fiscal_type'].selection)
                            .get(self.sale_fiscal_type), sequence.max_number_next))

                if inv.sale_fiscal_type in (
                        "fiscal", "gov", "special") and not inv.partner_id.vat:
                    raise UserError(_(
                        u"El cliente [{}]{} no tiene RNC/Céd, y es requerido"
                        "para este tipo de factura.").format(
                            inv.partner_id.id, inv.partner_id.name))

                if (inv.amount_untaxed_signed >= 250000 and
                        inv.sale_fiscal_type != 'unico' and
                        not inv.partner_id.vat):
                    raise UserError(_(
                        u"Si el monto es mayor a RD$250,000 el cliente debe "
                        u"tener un RNC o Céd para emitir la factura"))

            elif inv.type in ("in_invoice", "in_refund"):

                if not inv.reference and inv.journal_id.purchase_type in ('informal',
                                                                          'minor',
                                                                          'exterior'):
                    sequence1 = inv.journal_id.date_range_ids.filtered(
                        lambda seq: seq.sale_fiscal_type == inv.journal_id.purchase_type
                    )

                    if sequence1.number_next_actual > sequence1.max_number_next:
                        raise ValidationError(_(
                            u"Los comprobantes para {} se han agotado,"
                            " contacte al responsable de contabilidad ({}).").format(
                                dict(self._fields['sale_fiscal_type'].selection)
                                .get(self.sale_fiscal_type), sequence1.max_number_next))

                if inv.reference and inv.journal_id.purchase_type in (
                        'normal', 'informal', 'minor', 'exterior'):
                    if not inv.partner_id.vat:
                        raise ValidationError(_(
                            u"¡Para este tipo de Compra el Proveedor"
                            u" debe de tener un RNC/Cédula/NIT establecido!"))

                    if (inv.journal_id.purchase_type == 'exterior' and
                            inv.partner_id.country_id.code == 'DO'):
                        raise ValidationError(_(
                            u"¡Para Remesas al Exterior el Proveedor debe"
                            u" tener país diferente a República Dominicana!"))

            elif (inv.type == 'out_refund' and inv.journal_id.ncf_control and
                  inv.amount_untaxed_signed >= 250000 and
                  not inv.partner_id.vat):
                raise ValidationError(_("Para poder emitir una NC mayor a "
                                        " RD$250,000 se requiere que el "
                                        " cliente tenga RNC o Cédula."))

        return super(AccountInvoice, self).action_invoice_open()

    @api.model
    def _prepare_refund(self,
                        invoice,
                        date_invoice=None,
                        date=None,
                        description=None,
                        journal_id=None):
        res = super(AccountInvoice,
                    self)._prepare_refund(invoice,
                                          date_invoice=date_invoice,
                                          date=date,
                                          description=description,
                                          journal_id=journal_id)

        if self.type == "out_invoice" and self.journal_id.ncf_control:
            res.update({"reference": False, "origin_out": self.reference})

        if self._context.get("credit_note_supplier_ncf", False):
            res.update({
                "reference": self._context["credit_note_supplier_ncf"],
                "origin_out": self.reference,
                "expense_type": self.expense_type
            })
        return res

    @api.multi
    def invoice_validate(self):
        """ After all invoice validation routine, consume a NCF sequence and
            write it into reference field.
         """
        if not self.reference and (self.journal_id.ncf_control or
                                   self.journal_id.purchase_type in [
                                       'minor', 'informal', 'exterior'
                                   ]):
            sequence_id = self.journal_id.sequence_id
            if self.type == 'out_invoice':
                if self.is_nd:
                    self.reference = sequence_id.with_context(
                        sale_fiscal_type='debit_note')._next()
                else:
                    self.reference = sequence_id.with_context(
                        sale_fiscal_type=self.sale_fiscal_type)._next()
            elif self.type == 'out_refund':
                self.reference = sequence_id.with_context(
                    sale_fiscal_type='credit_note')._next()
            elif self.type == 'in_invoice':
                self.reference = sequence_id.with_context(
                    sale_fiscal_type=self.journal_id.purchase_type)._next()
            self.move_id.write({'ref': self.reference})

        return super(AccountInvoice, self).invoice_validate()

    @api.model
    def create(self, vals):
        if vals.get("sale_fiscal_type", None) == "fiscal":

            partner_id = self.env["res.partner"].browse(vals['partner_id'])
            vat = str(partner_id.vat)

            if partner_id and vat and vat.isdigit():
                if len(vat) not in [
                        9, 11
                ] or not (rnc.is_valid(vat) or cedula.is_valid(vat)):
                    raise ValidationError(_(
                        "El RNC del cliente NO pasó la validación en DGII\n\n"
                        "No es posible crear una factura con Crédito Fiscal "
                        "si el RNC del cliente es inválido."
                        "Verifique el RNC del cliente a fin de corregirlo y "
                        "vuelva a guardar la factura"))

        return super(AccountInvoice, self).create(vals)

    @api.multi
    def action_invoice_cancel(self):

        fiscal_invoices = self.filtered(
            lambda inv: inv.company_id.country_id.code == "DO"
            and inv.journal_id.ncf_control
        )
        if fiscal_invoices and not self.env.user.has_group(
                "ncf_manager.group_l10n_do_fiscal_invoice_cancel"
        ):
            raise AccessError("No tiene permitido cancelar Facturas Fiscales")

        return super(AccountInvoice, self).action_invoice_cancel()
