# TODO: poner authorship en todos los archivos .py (xml tamb?)

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fiscal_type_id = fields.Many2one(
        'account.fiscal.type',
        string="Fiscal Type",
        index=True,
    )
    fiscal_sequence_id = fields.Many2one(
        'account.fiscal.sequence',
        string="Fiscal Sequence",
        copy=False,
        compute='_compute_fiscal_sequence',
        store=True,
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
        store=True,
    )
    is_fiscal_invoice = fields.Boolean(
        related='journal_id.fiscal_journal',
    )
    internal_generate = fields.Boolean(
        related='fiscal_type_id.internal_generate',
    )
    fiscal_sequence_status = fields.Selection([
        ('no_fiscal', 'No fiscal'),
        ('fiscal_ok', 'Ok'),
        ('almost_no_sequence', 'Almost no sequence'),
        ('no_sequence', 'Depleted'),
    ],
        compute='_compute_fiscal_sequence_status',
    )
    is_debit_note = fields.Boolean()

    @api.multi
    @api.depends('journal_id', 'journal_id.fiscal_journal', 'fiscal_type_id',
                 'date_invoice', 'type', 'state', 'is_debit_note')
    def _compute_fiscal_sequence(self):
        for inv in self.filtered(lambda i: i.state == 'draft'):
            if inv.is_debit_note:
                debit_map = {'in_invoice': 'in_debit',
                             'out_invoice': 'out_debit'}
                fiscal_type = self.env['account.fiscal.type'].search([
                    ('type', '=', debit_map[inv.type])], limit=1)
                inv.fiscal_type_id = fiscal_type.id
            elif inv.type in ('out_refund', 'in_refund'):
                fiscal_type = self.env['account.fiscal.type'].search([
                    ('type', '=', inv.type)], limit=1)
                inv.fiscal_type_id = fiscal_type.id
            else:
                fiscal_type = inv.fiscal_type_id

            if inv.journal_id.fiscal_journal and fiscal_type and \
                    fiscal_type.internal_generate:

                inv.internal_generate = fiscal_type.internal_generate
                inv.fiscal_position_id = fiscal_type.fiscal_position_id

                domain = [
                    ('company_id', '=', inv.company_id.id),
                    ('fiscal_type_id', '=', fiscal_type.id),
                    ('state', '=', 'active'),
                ]
                if inv.date_invoice:
                    domain.append(('expiration_date', '>=', inv.date_invoice))
                else:
                    today = fields.Date.context_today(inv)
                    domain.append(('expiration_date', '>=', today))

                fiscal_sequence_id = inv.env['account.fiscal.sequence'].search(
                    domain,
                    order='expiration_date, id desc',
                    limit=1,
                )

                if not fiscal_sequence_id:
                    pass
                elif fiscal_sequence_id.state == 'active':
                    inv.fiscal_sequence_id = fiscal_sequence_id
                else:
                    inv.fiscal_sequence_id = False
            else:
                inv.fiscal_sequence_id = False

    @api.multi
    @api.depends('fiscal_sequence_id', 'fiscal_sequence_id.sequence_remaining',
                 'fiscal_sequence_id.remaining_percentage', 'state',
                 'journal_id.fiscal_journal')
    def _compute_fiscal_sequence_status(self):
        for inv in self:

            if not inv.journal_id.fiscal_journal or not inv.fiscal_sequence_id:
                inv.fiscal_sequence_status = 'no_fiscal'
            else:
                fs_id = inv.fiscal_sequence_id  # Fiscal Sequence
                remaining = fs_id.sequence_remaining
                remaining_percent = fs_id.remaining_percentage
                seq_length = fs_id.sequence_end - fs_id.sequence_start + 1

                consumed_percent = round(1 - (remaining / seq_length), 2) * 100

                if consumed_percent < remaining_percent:
                    inv.fiscal_sequence_status = 'fiscal_ok'
                elif remaining > 0 and consumed_percent >= remaining_percent:
                    inv.fiscal_sequence_status = 'almost_no_sequence'
                else:
                    inv.fiscal_sequence_status = 'no_sequence'

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if not self.is_fiscal_invoice:
            self.fiscal_type_id = False
            self.fiscal_sequence_id = False

        return super(AccountInvoice, self)._onchange_journal_id()

    @api.onchange('fiscal_type_id')
    def _onchange_fiscal_type(self):

        if self.is_fiscal_invoice and self.fiscal_type_id:
            fiscal_type = self.fiscal_type_id
            fiscal_type_journal = fiscal_type.journal_id
            if fiscal_type_journal and fiscal_type_journal != self.journal_id:
                self.journal_id = fiscal_type_journal

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):

        if self.is_fiscal_invoice:
            if self.type == 'out_invoice':
                if not self.fiscal_type_id:
                    self.fiscal_type_id = self.partner_id.sale_fiscal_type_id

            if self.type == 'in_invoice':
                self.fiscal_type_id = self.partner_id.purchase_fiscal_type_id
                self.expense_type = self.partner_id.expense_type

        return super(AccountInvoice, self)._onchange_partner_id()

    @api.multi
    def action_invoice_open(self):
        for inv in self:

            if inv.amount_untaxed == 0:
                raise UserError(_(u"You cannot validate an invoice whose "
                                  u"total amount is equal to 0"))

            if inv.is_fiscal_invoice:

                # Because a Fiscal Sequence can be depleted while an invoice
                # is waiting to be validated, compute fiscal_sequence_id again
                # on invoice validate.
                inv._compute_fiscal_sequence()

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
                            inv.fiscal_type_id.prefix != 'B12' and
                            not inv.partner_id.vat):
                        raise UserError(_(
                            u"if the invoice amount is greater than "
                            u"RD$250,000.00 "
                            u"the customer should have RNC or Céd"
                            u"for make invoice"))

                if not inv.reference and inv.fiscal_type_id.internal_generate:
                    inv.reference = inv.fiscal_sequence_id.get_fiscal_number()
                    inv.ncf_expiration_date = \
                        inv.fiscal_sequence_id.expiration_date

        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def invoice_print(self):

        # Companies which has installed l10n_do localization use
        # l10n_do fiscal invoice template
        l10n_do_coa = self.env.ref('l10n_do.do_chart_template')
        if self.journal_id.company_id.chart_template_id.id == l10n_do_coa.id:
            report_id = self.env.ref(
                'l10n_do_accounting.l10n_do_account_invoice')
            return report_id.report_action(self)

        return super(AccountInvoice, self).invoice_print()

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        context = dict(self._context or {})
        refund_type = context.get('refund_type')
        amount = context.get('amount')
        account = context.get('account')
        vendor_ref = context.get('vendor_ref')

        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)

        if refund_type and refund_type != 'full_refund':
            res['tax_line_ids'] = False
            res['invoice_line_ids'] = [(0, 0, {'name': description,
                                               'price_unit': amount,
                                               'account_id': account})]

        if not self.journal_id.fiscal_journal:
            return res

        fiscal_type = {'out_invoice': 'out_refund',
                       'in_invoice': 'in_refund'}

        fiscal_type_id = self.env['account.fiscal.type'].search(
            [('type', '=', fiscal_type[self.type])], limit=1)

        if not fiscal_type_id:
            raise ValidationError(_('No Fiscal Type found for Credit Note'))

        res.update({'reference': vendor_ref,
                    'origin_out': self.reference,
                    'income_type': self.income_type,
                    'expense_type': self.expense_type,
                    'fiscal_type_id': fiscal_type_id.id,
                    })

        return res

    @api.multi
    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None,
               journal_id=None):

        context = dict(self._context or {})
        refund_type = context.get('refund_type')
        amount = context.get('amount')
        account = context.get('account')
        vendor_ref = context.get('vendor_ref')

        if not refund_type:
            return super(AccountInvoice, self).refund(
                date_invoice=date_invoice, date=date, description=description,
                journal_id=journal_id)

        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self.with_context(
                refund_type=refund_type, amount=amount,
                account=account, vendor_ref=vendor_ref)._prepare_refund(
                invoice, date_invoice=date_invoice, date=date,
                description=description, journal_id=journal_id)
            refund_invoice = self.create(values)
            if invoice.type == 'out_invoice':
                message = _(
                    "This customer invoice credit note has been created from: "
                    "<a href=# data-oe-model=account.invoice data-oe-id=%d>%s"
                    "</a><br>Reason: %s") % (invoice.id, invoice.number,
                                             description)
            else:
                message = _(
                    "This vendor bill credit note has been created from: <a "
                    "href=# data-oe-model=account.invoice data-oe-id=%d>%s</a>"
                    "<br>Reason: %s") % (invoice.id, invoice.number,
                                         description)

            refund_invoice.message_post(body=message)
            refund_invoice._compute_fiscal_sequence()
            new_invoices += refund_invoice
        return new_invoices

    # TODO: a fiscal invoice cannot be validated if not fiscal_sequence_id
