# TODO: poner authorship en todos los archivos .py (xml tamb?)

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fiscal_type_id = fields.Many2one(
        'account.fiscal.type',
        string="Fiscal Type",
    )
    fiscal_sequence_id = fields.Many2one(
        'account.fiscal.sequence',
        string="Fiscal Sequence",
        copy=False,
    )
    income_type = fields.Selection(
        [('01', '01 - Ingresos por Operaciones (No Financieros)'),
         ('02', '02 - Ingresos Financieros'),
         ('03', '03 - Ingresos Extraordinarios'),
         ('04', '04 - Ingresos por Arrendamientos'),
         ('05', '05 - Ingresos por Venta de Activo Depreciable'),
         ('06', '06 - Otros Ingresos')],
        string='Income Type',
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
        string="Cost & Expense Type",
    )

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
        string="Annulment Type",
        copy=False,
    )
    origin_out = fields.Char(
        "Affects",
    )
    ncf_expiration_date = fields.Date(
        'Valid until',
        # compute="_compute_ncf_expiration_date",
        store=True,
    )
    is_fiscal_invoice = fields.Boolean(
        related='journal_id.fiscal_journal',
    )
    internal_generate = fields.Boolean(
        related='fiscal_type_id.internal_generate',
    )

    @api.onchange('journal_id')
    def _onchange_custom_journal(self):
        if not self.is_fiscal_invoice:
            self.fiscal_type_id = False

    @api.onchange('fiscal_type_id')
    def _onchange_fiscal_type(self):

        if self.is_fiscal_invoice and self.fiscal_type_id:
            fiscal_type = self.fiscal_type_id

            if fiscal_type.internal_generate:
                fiscal_sequence = self.env['account.fiscal.sequence']\
                    .search([('fiscal_type_id', '=', self.fiscal_type_id.id)
                             , ('state', '=', 'active'),
                             ('company_id', '=', self.company_id.id)],
                            limit=1)
                if not fiscal_sequence:
                    raise UserError(_(u"There is no current active NCF of {}"
                                      u", please create a new fiscal sequence "
                                      u"of type {}.").format(
                                    fiscal_type.name,
                                    fiscal_type.name))
                self.fiscal_sequence_id = fiscal_sequence.id

            self.internal_generate = fiscal_type.internal_generate
            self.fiscal_position_id = fiscal_type.fiscal_position_id
            if fiscal_type.journal_id:
                self.journal_id = fiscal_type.journal_id

    @api.onchange('partner_id')
    def _onchange_custom_partner_id(self):

        if self.is_fiscal_invoice:
            if self.type == 'out_invoice':
                if not self.fiscal_type_id:
                    self.fiscal_type_id = self.partner_id.sale_fiscal_type_id

            if self.type == 'in_invoice':
                self.fiscal_type_id = self.partner_id.purchase_fiscal_type_id
                self.expense_type = self.partner_id.expense_type

    @api.multi
    def action_invoice_open(self):
        for inv in self:

            if inv.amount_untaxed == 0:
                raise UserError(_(u"You cannot validate an invoice whose "
                                  u"total amount is equal to 0"))

            if inv.is_fiscal_invoice:

                if inv.type == 'out_invoice':
                    if not inv.partner_id.sale_fiscal_type_id:
                        inv.partner_id.sale_fiscal_type_id = inv.fiscal_type_id

                if inv.type == 'in_invoice':

                    if not inv.partner_id.purchase_fiscal_type_id:
                        inv.partner_id.purchase_fiscal_type_id = \
                            inv.fiscal_type_id
                    if not inv.partner_id.expense_type:
                        inv.partner_id.expense_type = inv.expense_type

                if inv.fiscal_type_id.required_document \
                        and not inv.partner_id.vat:
                    raise UserError(
                        _("Partner [{}] {} doesn't have RNC/Céd, "
                          "is required for NCF type {}").format(
                            inv.partner_id.id,
                            inv.partner_id.name,
                            inv.fiscal_type_id.name))

                if inv.type in ("out_invoice", "out_refund"):
                    if (inv.amount_untaxed_signed >= 250000 and
                            inv.fiscal_type_id.name != 'Único Ingreso' and
                            not inv.partner_id.vat):
                        raise UserError(_(
                            u"if the invoice amount is greater than "
                            u"RD$250,000.00 "
                            u"the costumer should have RNC or Céd"
                            u"for make invoice"))

                if not inv.reference and inv.fiscal_type_id.internal_generate:
                    inv.reference = inv.fiscal_sequence_id.get_fiscal_number()

        return super(AccountInvoice, self).action_invoice_open()
