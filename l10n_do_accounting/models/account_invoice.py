# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Yasmany Castillo <yasmany003@gmail.com>
# © 2018 José López <jlopez@indexa.do>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
# © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
# © 2018 Andrés Rodríguez <andres@iterativo.do>
# © 2019 Raul Ovalle <rovalle@guavana.com>


# This file is part of l10n_do_accounting.

# l10n_do_accounting is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# l10n_do_accounting is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fiscal_type_id = fields.Many2one(
        'account.fiscal.type',
        string="Fiscal Type",
    )
    fiscal_sequence_id = fields.Many2one(
        'account.fiscal.sequence',
        string="Fiscal Sequence"
    )
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

    ncf_expiration_date = fields.Date(
        'Válido hasta',
        # compute="_compute_ncf_expiration_date",
        store=True,
    )

    is_fiscal_invoice = fields.Boolean()
    internal_generate = fields.Boolean()
    origin_out = fields.Char("Afecta a")

    @api.onchange('journal_id')
    def _onchange_custom_journal_id(self):

        self.is_fiscal_invoice = self.journal_id.fiscal_journal

        if not self.is_fiscal_invoice:
            self.fiscal_type_id = False

    @api.onchange('fiscal_type_id')
    def _onchange_fiscal_type(self):

        self.internal_generate = self.fiscal_type_id.internal_generate
        self.fiscal_position_id = self.fiscal_type_id.fiscal_position_id

        if self.fiscal_type_id.journal_id:
            self.journal_id = self.fiscal_type_id.journal_id


    @api.onchange('partner_id')
    def _onchange_custom_partner_id(self):

        if self.is_fiscal_invoice:
            if self.type == 'out_invoice':
                self.fiscal_type_id = self.partner_id.sale_fiscal_type_id

            if self.type == 'in_invoice':
                self.fiscal_type_id = self.partner_id.purchase_fiscal_type_id
                self.expense_type = self.expense_type

    @api.multi
    def action_invoice_open(self):


        for inv in self:

            if inv.amount_untaxed == 0:
                raise UserError(_(u"You cannot validate an invoice whose total amount is equal to 0"))

            if inv.is_fiscal_invoice:

                if inv.type == 'out_invoice':
                    if not inv.partner_id.sale_fiscal_type_id:
                        inv.partner_id.sale_fiscal_type_id = inv.fiscal_type_id

                if inv.type == 'in_invoice':
                    if not inv.partner_id.purchase_fiscal_type_id:
                        inv.partner_id.purchase_fiscal_type_id = inv.fiscal_type_id
                    if not inv.partner_id.expense_type:
                        inv.partner_id.expense_type = inv.expense_type

                if inv.fiscal_type_id.required_document and not inv.partner_id.vat:
                    raise UserError(_("Partner [{}] {} doesn't have RNC/Céd, is required for this fiscal type").format(
                        inv.partner_id.id, inv.partner_id.name))

                if inv.type in ("out_invoice", "out_refund"):
                    if (inv.amount_untaxed_signed >= 250000 and
                            inv.fiscal_type_id.name != 'Único Ingreso' and
                            not inv.partner_id.vat):
                        raise UserError(_(
                            u"if the invoice amount is greater than RD$250,000.00 the costumer should have RNC or Céd"
                            u"for make invoice"))

        return super(AccountInvoice, self).action_invoice_open()