# Part of Domincana Premium.
# See LICENSE file for full copyright and licensing details.
# © 2018 José López <jlopez@indexa.do>
# © 2018 Gustavo Valverde <gustavo@iterativo.do>

import calendar
import base64
from datetime import datetime as dt

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

try:
    import pycountry
except ImportError:
    raise ImportError(
        _("This module needs pycountry to get 609 ISO 3166 "
          "country codes. Please install pycountry on your system. "
          "(See requirements file)"))


class DgiiReportSaleSummary(models.Model):
    _name = 'dgii.reports.sale.summary'
    _description = "DGII Report Sale Summary"
    _order = 'sequence'

    name = fields.Char()
    sequence = fields.Integer()
    qty = fields.Integer()
    amount = fields.Monetary()
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    dgii_report_id = fields.Many2one('dgii.reports', ondelete='cascade')


class DgiiReport(models.Model):
    _name = 'dgii.reports'
    _description = "DGII Report"
    _inherit = ['mail.thread']

    @api.multi
    def _compute_previous_report_pending(self):
        for report in self:
            previous = self.search([('company_id', '=', report.company_id.id),
                                    ('state', 'in', ('draft', 'generated')),
                                    ('id', '!=', self.id)],
                                   order='create_date asc',
                                   limit=1)
            if previous:
                previous_date = dt.strptime('01/' + previous.name,
                                            '%d/%m/%Y').date()
                current_date = dt.strptime('01/' + self.name,
                                           '%d/%m/%Y').date()
                report.previous_report_pending = True if previous_date < \
                    current_date else False
            else:
                report.previous_report_pending = False

    name = fields.Char(string='Period', required=True, size=7)
    state = fields.Selection([('draft', 'New'), ('error', 'With error'),
                              ('generated', 'Generated'), ('sent', 'Sent')],
                             default='draft',
                             track_visibility='onchange',
                             copy=False)
    previous_balance = fields.Float('Previous balance', copy=False)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 default=lambda self: self.env.user.company_id,
                                 required=True)
    previous_report_pending = fields.Boolean(
        compute='_compute_previous_report_pending')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name, company_id)',
         _("You cannot have more than one report by period."))
    ]

    @api.multi
    def _compute_606_fields(self):
        for rec in self:
            data = {
                'purchase_records': 0,
                'service_total_amount': 0,
                'good_total_amount': 0,
                'purchase_invoiced_amount': 0,
                'purchase_invoiced_itbis': 0,
                'purchase_withholded_itbis': 0,
                'cost_itbis': 0,
                'advance_itbis': 0,
                'income_withholding': 0,
                'purchase_selective_tax': 0,
                'purchase_other_taxes': 0,
                'purchase_legal_tip': 0
            }
            purchase_line_ids = self.env['dgii.reports.purchase.line'].search([
                ('dgii_report_id', '=', rec.id)
            ])
            for inv in purchase_line_ids:
                data['purchase_records'] += 1
                data['service_total_amount'] += inv.service_total_amount
                data['good_total_amount'] += inv.good_total_amount
                data['purchase_invoiced_amount'] += inv.invoiced_amount
                data['purchase_invoiced_itbis'] += inv.invoiced_itbis
                data['purchase_withholded_itbis'] += inv.withholded_itbis
                data['cost_itbis'] += inv.cost_itbis
                data['advance_itbis'] += inv.advance_itbis
                data['income_withholding'] += inv.income_withholding
                data['purchase_selective_tax'] += inv.selective_tax
                data['purchase_other_taxes'] += inv.other_taxes
                data['purchase_legal_tip'] += inv.legal_tip

            rec.purchase_records = abs(data['purchase_records'])
            rec.service_total_amount = abs(data['service_total_amount'])
            rec.good_total_amount = abs(data['good_total_amount'])
            rec.purchase_invoiced_amount = abs(
                data['purchase_invoiced_amount'])
            rec.purchase_invoiced_itbis = abs(data['purchase_invoiced_itbis'])
            rec.purchase_withholded_itbis = abs(
                data['purchase_withholded_itbis'])
            rec.cost_itbis = abs(data['cost_itbis'])
            rec.advance_itbis = abs(data['advance_itbis'])
            rec.income_withholding = abs(data['income_withholding'])
            rec.purchase_selective_tax = abs(data['purchase_selective_tax'])
            rec.purchase_other_taxes = abs(data['purchase_other_taxes'])
            rec.purchase_legal_tip = abs(data['purchase_legal_tip'])

    @api.multi
    def _compute_607_fields(self):
        for rec in self:
            data = {
                'sale_records': 0,
                'sale_invoiced_amount': 0,
                'sale_invoiced_itbis': 0,
                'sale_withholded_itbis': 0,
                'sale_withholded_isr': 0,
                'sale_selective_tax': 0,
                'sale_other_taxes': 0,
                'sale_legal_tip': 0
            }
            sale_line_ids = self.env['dgii.reports.sale.line'].search([
                ('dgii_report_id', '=', rec.id)
            ])
            for inv in sale_line_ids:
                data['sale_records'] += 1
                data['sale_invoiced_amount'] += inv.invoiced_amount
                data['sale_invoiced_itbis'] += inv.invoiced_itbis
                data['sale_withholded_itbis'] += inv.third_withheld_itbis
                data['sale_withholded_isr'] += inv.third_income_withholding
                data['sale_selective_tax'] += inv.selective_tax
                data['sale_other_taxes'] += inv.other_taxes
                data['sale_legal_tip'] += inv.legal_tip

            rec.sale_records = abs(data['sale_records'])
            rec.sale_invoiced_amount = abs(data['sale_invoiced_amount'])
            rec.sale_invoiced_itbis = abs(data['sale_invoiced_itbis'])
            rec.sale_withholded_itbis = abs(data['sale_withholded_itbis'])
            rec.sale_withholded_isr = abs(data['sale_withholded_isr'])
            rec.sale_selective_tax = abs(data['sale_selective_tax'])
            rec.sale_other_taxes = abs(data['sale_other_taxes'])
            rec.sale_legal_tip = abs(data['sale_legal_tip'])

    @api.multi
    def _compute_608_fields(self):
        for rec in self:
            cancel_line_ids = self.env['dgii.reports.cancel.line'].search([
                ('dgii_report_id', '=', rec.id)
            ])
            rec.cancel_records = len(cancel_line_ids)

    @api.multi
    def _compute_609_fields(self):
        for rec in self:
            data = {
                'exterior_records': 0,
                'presumed_income': 0,
                'exterior_withholded_isr': 0,
                'exterior_invoiced_amount': 0
            }
            external_line_ids = self.env['dgii.reports.exterior.line'].search([
                ('dgii_report_id', '=', rec.id)
            ])
            for inv in external_line_ids:
                data['exterior_records'] += 1
                data['presumed_income'] += inv.presumed_income
                data['exterior_withholded_isr'] += inv.withholded_isr
                data['exterior_invoiced_amount'] += inv.invoiced_amount

            rec.exterior_records = abs(data['exterior_records'])
            rec.presumed_income = abs(data['presumed_income'])
            rec.exterior_withholded_isr = abs(data['exterior_withholded_isr'])
            rec.exterior_invoiced_amount = abs(
                data['exterior_invoiced_amount'])

    # 606
    purchase_records = fields.Integer(compute='_compute_606_fields')
    service_total_amount = fields.Monetary(compute='_compute_606_fields')
    good_total_amount = fields.Monetary(compute='_compute_606_fields')
    purchase_invoiced_amount = fields.Monetary(compute='_compute_606_fields')
    purchase_invoiced_itbis = fields.Monetary(compute='_compute_606_fields')
    purchase_withholded_itbis = fields.Monetary(compute='_compute_606_fields')
    cost_itbis = fields.Monetary(compute='_compute_606_fields')
    advance_itbis = fields.Monetary(compute='_compute_606_fields')
    income_withholding = fields.Monetary(compute='_compute_606_fields')
    purchase_selective_tax = fields.Monetary(compute='_compute_606_fields')
    purchase_other_taxes = fields.Monetary(compute='_compute_606_fields')
    purchase_legal_tip = fields.Monetary(compute='_compute_606_fields')
    purchase_filename = fields.Char()
    purchase_binary = fields.Binary(string='606 file')

    # 607
    sale_records = fields.Integer(compute='_compute_607_fields')
    sale_invoiced_amount = fields.Float(compute='_compute_607_fields')
    sale_invoiced_itbis = fields.Float(compute='_compute_607_fields')
    sale_withholded_itbis = fields.Float(compute='_compute_607_fields')
    sale_withholded_isr = fields.Float(compute='_compute_607_fields')
    sale_selective_tax = fields.Float(compute='_compute_607_fields')
    sale_other_taxes = fields.Float(compute='_compute_607_fields')
    sale_legal_tip = fields.Float(compute='_compute_607_fields')
    sale_filename = fields.Char()
    sale_binary = fields.Binary(string='607 file')

    # 608
    cancel_records = fields.Integer(compute='_compute_608_fields')
    cancel_filename = fields.Char()
    cancel_binary = fields.Binary(string='608 file')

    # 609
    exterior_records = fields.Integer(compute='_compute_609_fields')
    presumed_income = fields.Float(compute='_compute_609_fields')
    exterior_withholded_isr = fields.Float(compute='_compute_609_fields')
    exterior_invoiced_amount = fields.Float(compute='_compute_609_fields')
    exterior_filename = fields.Char()
    exterior_binary = fields.Binary(string='609 file')

    # IT-1
    ncf_sale_summary_ids = fields.One2many('dgii.reports.sale.summary',
                                           'dgii_report_id',
                                           string='Operations by NCF type',
                                           copy=False)
    cash = fields.Monetary('Cash', copy=False)
    bank = fields.Monetary('Check / Transfer / Deposit', copy=False)
    card = fields.Monetary('Credit Card / Debit Card', copy=False)
    credit = fields.Monetary('Credit', copy=False)
    bond = fields.Monetary('Gift certificates or vouchers', copy=False)
    swap = fields.Monetary('Swap', copy=False)
    others = fields.Monetary('Other Sale Forms', copy=False)
    sale_type_total = fields.Monetary('Total', copy=False)

    opr_income = fields.Monetary('Operations Income (No-Financial)',
                                 copy=False)
    fin_income = fields.Monetary('Financial Income', copy=False)
    ext_income = fields.Monetary('Extraordinary Income', copy=False)
    lea_income = fields.Monetary('Lease Income', copy=False)
    ast_income = fields.Monetary('Depreciable Assets Income', copy=False)
    otr_income = fields.Monetary('Others Income', copy=False)
    income_type_total = fields.Monetary('Total', copy=False)

    # General Summary of Consumer Invoices
    csmr_ncf_qty = fields.Integer('Issued Consumer NCF Qty', copy=False)
    csmr_ncf_total_amount = fields.Monetary('Invoiced Amount Total',
                                            copy=False)
    csmr_ncf_total_itbis = fields.Monetary('Invoiced ITBIS Total', copy=False)
    csmr_ncf_total_isc = fields.Monetary('Selective Tax', copy=False)
    csmr_ncf_total_othr = fields.Monetary('Other Taxes Total', copy=False)
    csmr_ncf_total_lgl_tip = fields.Monetary('Legal Tip Total', copy=False)

    # General Summary of Consumer Invoices - Sale Form
    csmr_cash = fields.Monetary('Cash', copy=False)
    csmr_bank = fields.Monetary('Check / Transfer / Deposit', copy=False)
    csmr_card = fields.Monetary('Credit Card / Debit Card', copy=False)
    csmr_credit = fields.Monetary('Credit', copy=False)
    csmr_bond = fields.Monetary('Gift certificates or vouchers', copy=False)
    csmr_swap = fields.Monetary('Swap', copy=False)
    csmr_others = fields.Monetary('Other Sale Forms', copy=False)

    def _get_country_number(self, partner_id):
        """
        Returns ISO 3166 country number from partner
        country code
        """
        res = False
        if not partner_id.country_id:
            return False
        try:
            country = pycountry.countries.get(
                alpha_2=partner_id.country_id.code)
            res = country.numeric
        except AttributeError:
            return res
        return res

    def _validate_date_format(self, date):
        """Validate date format <MM/YYYY>"""
        if date is not None:
            error = _('Error. Date format must be MM/YYYY')
            if len(date) == 7:
                try:
                    dt.strptime(date, '%m/%Y')
                except ValueError:
                    raise ValidationError(error)
            else:
                raise ValidationError(error)

    @api.model
    def create(self, vals):
        self._validate_date_format(vals.get('name'))

        return super(DgiiReport, self).create(vals)

    @api.multi
    def write(self, vals):
        self._validate_date_format(vals.get('name'))

        return super(DgiiReport, self).write(vals)

    @staticmethod
    def get_date_tuple(date):
        return date.year, date.month

    def _get_pending_invoices(self, types):

        period = dt.strptime(self.name, '%m/%Y')

        month, year = self.name.split('/')
        start_date = '{}-{}-{}'.format(
            year, month,
            calendar.monthrange(int(year), int(month))[1])
        invoice_ids = self.env['account.invoice'].search([
            ('fiscal_status', '=', 'normal'),
            ('state', '=', 'paid'),
            ('payment_date', '<=', start_date),
            ('company_id', '=', self.company_id.id),
            ('type', 'in', types),
        ]).filtered(lambda inv: self.get_date_tuple(inv.payment_date) ==
                    (period.year, period.month))

        return invoice_ids

    def _get_invoices(self, states, types):
        """
        Given rec and state, return a recordset of invoices
        :param state: a list of invoice state
        :param type: a list of invoice type
        :return: filtered invoices
        """
        month, year = self.name.split('/')
        last_day = calendar.monthrange(int(year), int(month))[1]
        start_date = '{}-{}-01'.format(year, month)
        end_date = '{}-{}-{}'.format(year, month, last_day)

        invoice_ids = self.env['account.invoice'].search(
            [('date_invoice', '>=', start_date),
             ('date_invoice', '<=', end_date),
             ('company_id', '=', self.company_id.id),
             ('state', 'in', states),
             ('type', 'in', types)],
            order='date_invoice asc').filtered(
                lambda inv: (inv.journal_id.purchase_type != 'others') or
                (inv.journal_id.ncf_control is True))

        # Append pending invoces (fiscal_status = Partial, state = Paid)
        invoice_ids |= self._get_pending_invoices(types)

        return invoice_ids

    def formated_rnc_cedula(self, vat):
        if vat:
            if len(vat) in [9, 11]:
                id_type = 1 if len(vat) == 9 else 2
                return (vat.strip().replace('-', ''),
                        id_type) if not vat.isspace() else False
            else:
                return False
        else:
            return False

    def _get_formated_date(self, date):

        return dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d') \
            if isinstance(date, str) else date.strftime('%Y%m%d') \
            if date else ""

    def _get_formated_amount(self, amount):

        return str('{:.2f}'.format(abs(amount))).ljust(12)

    def process_606_report_data(self, values):

        RNC = str(values['rnc_cedula'] if values['rnc_cedula'] else "")
        ID_TYPE = str(values['identification_type']
                      if values['identification_type'] else "").ljust(1)
        EXP_TYPE = str(
            values['expense_type'] if values['expense_type'] else "").ljust(2)
        NCF = str(values['fiscal_invoice_number']).ljust(11)
        NCM = str(values['modified_invoice_number']
                  if values['modified_invoice_number'] else "").ljust(19)
        INV_DATE = str(self._get_formated_date(
            values['invoice_date'])).ljust(8)
        PAY_DATE = str(self._get_formated_date(
            values['payment_date'])).ljust(8)
        SERV_AMOUNT = self._get_formated_amount(values['service_total_amount'])
        GOOD_AMOUNT = self._get_formated_amount(values['good_total_amount'])
        INV_AMOUNT = self._get_formated_amount(values['invoiced_amount'])
        INV_ITBIS = self._get_formated_amount(values['invoiced_itbis'])
        WH_ITBIS = self._get_formated_amount(values['withholded_itbis'])
        PROP_ITBIS = self._get_formated_amount(values['proportionality_tax'])
        COST_ITBIS = self._get_formated_amount(values['cost_itbis'])
        ADV_ITBIS = self._get_formated_amount(values['advance_itbis'])
        PP_ITBIS = ''
        WH_TYPE = str(values['isr_withholding_type']
                      if values['isr_withholding_type'] else "")
        INC_WH = self._get_formated_amount(values['income_withholding'])
        PP_ISR = ''
        ISC = self._get_formated_amount(values['selective_tax'])
        OTHR = self._get_formated_amount(values['other_taxes'])
        LEG_TIP = self._get_formated_amount(values['legal_tip'])
        PAY_FORM = str(
            values['payment_type'] if values['payment_type'] else "").ljust(2)

        return "|".join([
            RNC, ID_TYPE, EXP_TYPE, NCF, NCM, INV_DATE, PAY_DATE, SERV_AMOUNT,
            GOOD_AMOUNT, INV_AMOUNT, INV_ITBIS, WH_ITBIS, PROP_ITBIS,
            COST_ITBIS, ADV_ITBIS, PP_ITBIS, WH_TYPE, INC_WH, PP_ISR, ISC,
            OTHR, LEG_TIP, PAY_FORM
        ])

    def _generate_606_txt(self, records, qty):

        company_vat = self.company_id.vat
        period = dt.strptime(self.name.replace('/', ''),
                             '%m%Y').strftime('%Y%m')

        header = "606|{}|{}|{}".format(
            str(company_vat).ljust(11), period, qty) + '\n'
        data = header + records

        file_path = '/tmp/DGII_606_{}_{}.txt'.format(company_vat, period)
        with open(file_path, 'w', encoding="utf-8", newline='\r\n') as txt_606:
            txt_606.write(str(data))

        self.write({
            'purchase_filename': file_path.replace('/tmp/', ''),
            'purchase_binary': base64.b64encode(open(file_path, 'rb').read())
        })

    def _include_in_current_report(self, invoice):
        """
        Evaluate if invoice was paid in current month or
        was included in a previous period.
        New reported invoices should not include any
        withholding amount nor payment date
        if payment was made after current period.
        :param invoice: account.invoice object
        :return: boolean
        """
        if not invoice.payment_date:
            return False

        payment_date = invoice.payment_date
        period = dt.strptime(self.name, '%m/%Y')
        same_minor_period = (payment_date.month,
                             payment_date.year) <= (period.month, period.year)

        return True if (payment_date and same_minor_period) else False

    @api.multi
    def _compute_606_data(self):
        for rec in self:
            PurchaseLine = self.env['dgii.reports.purchase.line']
            PurchaseLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(['open', 'in_payment', 'paid'],
                                             ['in_invoice', 'in_refund'])

            line = 0
            report_data = ''
            for inv in invoice_ids:
                inv.fiscal_status = 'blocked' if not inv.fiscal_status else \
                    inv.fiscal_status
                line += 1
                rnc_ced = self.formated_rnc_cedula(
                    inv.partner_id.vat
                ) if inv.purchase_type != 'exterior' else \
                    self.formated_rnc_cedula(
                    inv.company_id.vat)
                show_payment_date = self._include_in_current_report(inv)
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'rnc_cedula': rnc_ced[0] if rnc_ced else False,
                    'identification_type': rnc_ced[1] if rnc_ced else False,
                    'expense_type': inv.expense_type
                    if inv.expense_type else False,
                    'fiscal_invoice_number': inv.reference,
                    'modified_invoice_number': inv.origin_out if
                    inv.type == 'in_refund' else False,
                    'invoice_date': inv.date_invoice,
                    'payment_date': inv.payment_date if
                    show_payment_date else False,
                    'service_total_amount': inv.service_total_amount,
                    'good_total_amount': inv.good_total_amount,
                    'invoiced_amount': inv.amount_untaxed_signed,
                    'invoiced_itbis': inv.invoiced_itbis,
                    'proportionality_tax': inv.proportionality_tax,
                    'cost_itbis': inv.cost_itbis,
                    'advance_itbis': inv.advance_itbis,
                    'purchase_perceived_itbis': 0,  # Falta computar en la fact
                    'purchase_perceived_isr': 0,  # Falta computarlo en la fact
                    'isr_withholding_type': inv.isr_withholding_type,
                    'withholded_itbis': inv.withholded_itbis if
                    show_payment_date else 0,
                    'income_withholding': inv.income_withholding if
                    show_payment_date else 0,
                    'selective_tax': inv.selective_tax,
                    'other_taxes': inv.other_taxes,
                    'legal_tip': inv.legal_tip,
                    'payment_type': inv.payment_form,
                    'invoice_partner_id': inv.partner_id.id,
                    'invoice_id': inv.id,
                    'credit_note': True if inv.type == 'in_refund' else False
                }
                PurchaseLine.create(values)
                report_data += self.process_606_report_data(values) + '\n'
            self._generate_606_txt(report_data, line)

    def _get_payments_dict(self):
        return {
            'cash': 0,
            'bank': 0,
            'card': 0,
            'credit': 0,
            'swap': 0,
            'bond': 0,
            'others': 0
        }

    def _convert_to_user_currency(self, base_currency, amount):
        context = dict(self._context or {})
        user_currency_id = self.env.user.company_id.currency_id
        base_currency_id = base_currency
        ctx = context.copy()
        return base_currency_id.with_context(ctx).compute(
            amount, user_currency_id)

    @staticmethod
    def include_payment(invoice_id, payment_id):
        """ Returns True if payment date is on or before current period """

        p_date = payment_id.payment_date
        i_date = invoice_id.date_invoice

        return True if (p_date.year <= i_date.year) and (
            p_date.month <= i_date.month) else False

    def _get_sale_payments_forms(self, invoice_id):
        payments_dict = self._get_payments_dict()
        Payment = self.env['account.payment']

        if invoice_id.type == 'out_invoice':
            for payment in invoice_id._get_invoice_payment_widget():
                payment_id = Payment.browse(payment['account_payment_id'])
                if payment_id:
                    key = payment_id.journal_id.payment_form
                    if key:
                        if self.include_payment(invoice_id, payment_id):
                            payments_dict[
                                key] += self._convert_to_user_currency(
                                    invoice_id.currency_id, payment['amount'])
                        else:
                            payments_dict[
                                'credit'] += self._convert_to_user_currency(
                                    invoice_id.currency_id, payment['amount'])
                else:
                    # Do not consider credit notes as swap payments
                    continue
            payments_dict['credit'] += self._convert_to_user_currency(
                invoice_id.currency_id, invoice_id.residual)
        else:
            payments_dict['credit'] += self._convert_to_user_currency(
                invoice_id.currency_id, invoice_id.residual)

        return payments_dict

    def _get_607_operations_dict(self):
        return {
            'fiscal': {
                'sequence': 1,
                'qty': 0,
                'amount': 0,
                'name': 'COMPROBANTE VÁLIDO PARA CRÉDITO FISCAL',
                'dgii_report_id': self.id
            },
            'final': {
                'sequence': 2,
                'qty': 0,
                'amount': 0,
                'name': 'COMPROBANTE CONSUMIDOR FINAL',
                'dgii_report_id': self.id
            },
            'export': {
                'sequence': 3,
                'qty': 0,
                'amount': 0,
                'name': 'COMPROBANTE DE EXPORTACIONES',
                'dgii_report_id': self.id
            },
            'nd': {
                'sequence': 4,
                'qty': 0,
                'amount': 0,
                'name': 'COMPROBANTES NOTA DE DÉBITO',
                'dgii_report_id': self.id
            },
            'nc': {
                'sequence': 5,
                'qty': 0,
                'amount': 0,
                'name': 'COMPROBANTES NOTA DE CRÉDITO',
                'dgii_report_id': self.id
            },
            'unico': {
                'sequence': 6,
                'qty': 0,
                'amount': 0,
                'name': 'COMPROBANTE REGISTRO ÚNICO DE INGRESOS',
                'dgii_report_id': self.id
            },
            'special': {
                'sequence': 8,
                'qty': 0,
                'amount': 0,
                'name': 'COMPROBANTE REGISTRO REGIMENES ESPECIALES',
                'dgii_report_id': self.id
            },
            'gov': {
                'sequence': 9,
                'qty': 0,
                'amount': 0,
                'name': 'COMPROBANTES GUBERNAMENTALES',
                'dgii_report_id': self.id
            },
            'positive': {
                'sequence': 10,
                'qty': 0,
                'amount': 0,
                'name': 'OTRAS OPERACIONES (POSITIVAS) - *PENDIENTE*',
                'dgii_report_id': self.id
            },
            'negative': {
                'sequence': 11,
                'qty': 0,
                'amount': 0,
                'name': 'OTRAS OPERACIONES (NEGATIVAS) - *PENDIENTE*',
                'dgii_report_id': self.id
            },
        }

    def _process_op_dict(self, args, invoice):
        op_dict = args
        if invoice.sale_fiscal_type and invoice.type != 'out_refund':
            op_dict[invoice.sale_fiscal_type]['qty'] += 1
            op_dict[invoice.sale_fiscal_type][
                'amount'] += invoice.amount_untaxed_signed
        if invoice.type == 'out_refund' and not invoice.is_nd:
            op_dict['nc']['qty'] += 1
            op_dict['nc']['amount'] += invoice.amount_untaxed_signed
        if invoice.is_nd:
            op_dict['nd']['qty'] += 1
            op_dict['nd']['amount'] += invoice.amount_untaxed_signed

        return op_dict

    @api.multi
    def _set_payment_form_fields(self, payments_dict):
        for rec in self:
            rec.cash = payments_dict.get('cash')
            rec.bank = payments_dict.get('bank')
            rec.card = payments_dict.get('card')
            rec.credit = payments_dict.get('credit')
            rec.bond = payments_dict.get('bond')
            rec.swap = payments_dict.get('swap')
            rec.others = payments_dict.get('others')
            rec.sale_type_total = rec.cash + rec.bank + \
                rec.card + rec.credit + rec.bond + rec.swap + rec.others

    def _get_income_type_dict(self):
        return {'01': 0, '02': 0, '03': 0, '04': 0, '05': 0, '06': 0}

    def _process_income_dict(self, args, invoice):
        income_dict = args
        if invoice.income_type:
            income_dict[invoice.income_type] += invoice.amount_untaxed_signed
        return income_dict

    @api.multi
    def _set_income_type_fields(self, income_dict):
        for rec in self:
            rec.opr_income = income_dict.get('01')
            rec.fin_income = income_dict.get('02')
            rec.ext_income = income_dict.get('03')
            rec.lea_income = income_dict.get('04')
            rec.ast_income = income_dict.get('05')
            rec.otr_income = income_dict.get('06')
            rec.income_type_total = \
                rec.opr_income + rec.fin_income + rec.ext_income + \
                rec.lea_income + rec.ast_income + rec.otr_income

    def process_607_report_data(self, values):

        RNC = str(values['rnc_cedula'] if values['rnc_cedula'] else "").ljust(
            11)
        ID_TYPE = str(values['identification_type']
                      if values['identification_type'] else "")
        NCF = str(values['fiscal_invoice_number']).ljust(11)
        NCM = str(values['modified_invoice_number']
                  if values['modified_invoice_number'] else "").ljust(19)
        INCOME_TYPE = str(values['income_type']).ljust(2)
        INV_DATE = str(self._get_formated_date(
            values['invoice_date'])).ljust(8)
        WH_DATE = str(self._get_formated_date(
            values['withholding_date'])).ljust(8)
        INV_AMOUNT = self._get_formated_amount(values['invoiced_amount'])
        INV_ITBIS = self._get_formated_amount(values['invoiced_itbis'])
        WH_ITBIS = self._get_formated_amount(values['third_withheld_itbis'])
        PRC_ITBIS = ''
        WH_ISR = self._get_formated_amount(values['third_income_withholding'])
        PCR_ISR = ''
        ISC = self._get_formated_amount(values['selective_tax'])
        OTH_TAX = self._get_formated_amount(values['other_taxes'])
        LEG_TIP = self._get_formated_amount(values['legal_tip'])
        CASH = self._get_formated_amount(values['cash'])
        BANK = self._get_formated_amount(values['bank'])
        CARD = self._get_formated_amount(values['card'])
        CRED = self._get_formated_amount(values['credit'])
        SWAP = self._get_formated_amount(values['swap'])
        BOND = self._get_formated_amount(values['bond'])
        OTHR = self._get_formated_amount(values['others'])

        return "|".join([
            RNC, ID_TYPE, NCF, NCM, INCOME_TYPE, INV_DATE, WH_DATE, INV_AMOUNT,
            INV_ITBIS, WH_ITBIS, PRC_ITBIS, WH_ISR, PCR_ISR, ISC, OTH_TAX,
            LEG_TIP, CASH, BANK, CARD, CRED, SWAP, BOND, OTHR
        ])

    def _generate_607_txt(self, records, qty):

        company_vat = self.company_id.vat
        period = \
            dt.strptime(self.name.replace('/', ''), '%m%Y').strftime('%Y%m')

        header = "607|{}|{}|{}".format(
            str(company_vat).ljust(11), period, qty) + '\n'
        data = header + records

        file_path = '/tmp/DGII_607_{}_{}.txt'.format(company_vat, period)
        with open(file_path, 'w', encoding="utf-8", newline='\r\n') as txt_607:
            txt_607.write(str(data))

        self.write({
            'sale_filename': file_path.replace('/tmp/', ''),
            'sale_binary': base64.b64encode(open(file_path, 'rb').read())
        })

    def _get_csmr_vals_dict(self):
        return {
            'csmr_ncf_qty': 0,
            'csmr_ncf_total_amount': 0,
            'csmr_ncf_total_itbis': 0,
            'csmr_ncf_total_isc': 0,
            'csmr_ncf_total_othr': 0,
            'csmr_ncf_total_lgl_tip': 0,
            'csmr_cash': 0,
            'csmr_bank': 0,
            'csmr_card': 0,
            'csmr_credit': 0,
            'csmr_bond': 0,
            'csmr_swap': 0,
            'csmr_others': 0
        }

    def _set_csmr_fields_vals(self, csmr_dict):
        self.write(csmr_dict)

    @api.multi
    def _compute_607_data(self):
        for rec in self:
            SaleLine = self.env['dgii.reports.sale.line']
            SaleLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(['open', 'in_payment', 'paid'],
                                             ['out_invoice', 'out_refund'])

            line = 0
            excluded_line = line
            op_dict = self._get_607_operations_dict()
            payment_dict = self._get_payments_dict()
            income_dict = self._get_income_type_dict()
            csmr_dict = self._get_csmr_vals_dict()

            report_data = ''
            for inv in invoice_ids:
                op_dict = self._process_op_dict(op_dict, inv)
                income_dict = self._process_income_dict(income_dict, inv)
                inv.fiscal_status = \
                    'blocked' if not inv.fiscal_status else inv.fiscal_status
                rnc_ced = self.formated_rnc_cedula(
                    inv.partner_id.vat
                ) if inv.sale_fiscal_type != 'unico' \
                    else self.formated_rnc_cedula(inv.company_id.vat)
                show_payment_date = self._include_in_current_report(inv)
                payments = self._get_sale_payments_forms(inv)
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'rnc_cedula': rnc_ced[0] if rnc_ced else False,
                    'identification_type': rnc_ced[1] if rnc_ced else False,
                    'fiscal_invoice_number': inv.reference,
                    'modified_invoice_number':
                        inv.origin_out if inv.origin_out and
                        inv.origin_out[-10:-8] in ['01', '02', '14', '15'] else
                        False,
                    'income_type': inv.income_type,
                    'invoice_date': inv.date_invoice,
                    'withholding_date': inv.payment_date if (
                        inv.type != 'out_refund' and
                        show_payment_date) else False,
                    'invoiced_amount': inv.amount_untaxed_signed,
                    'invoiced_itbis': inv.invoiced_itbis,
                    'third_withheld_itbis': inv.third_withheld_itbis
                        if show_payment_date else 0,
                    'perceived_itbis': 0,  # Pendiente
                    'third_income_withholding': inv.third_income_withholding
                        if show_payment_date else 0,
                    'perceived_isr': 0,  # Pendiente
                    'selective_tax': inv.selective_tax,
                    'other_taxes': inv.other_taxes,
                    'legal_tip': inv.legal_tip,
                    'invoice_partner_id': inv.partner_id.id,
                    'invoice_id': inv.id,
                    'credit_note': True if inv.type == 'out_refund' else False,
                    'cash': payments.get('cash') * -1 if
                        inv.type == 'out_refund' else payments.get('cash'),
                    'bank': payments.get('bank') * -1 if
                        inv.type == 'out_refund' else payments.get('bank'),
                    'card': payments.get('card') * -1 if
                        inv.type == 'out_refund' else payments.get('card'),
                    'credit': payments.get('credit') * -1 if
                        inv.type == 'out_refund' else payments.get('credit'),
                    'swap': payments.get('swap') * -1 if
                        inv.type == 'out_refund' else payments.get('swap'),
                    'bond': payments.get('bond') * -1 if
                        inv.type == 'out_refund' else payments.get('bond'),
                    'others': payments.get('others') * -1 if
                    inv.type == 'out_refund' else payments.get('others')
                }

                if str(values['fiscal_invoice_number'])[-10:-8] == '02':
                    csmr_dict['csmr_ncf_qty'] += 1
                    csmr_dict['csmr_ncf_total_amount'] += \
                        values['invoiced_amount']
                    csmr_dict['csmr_ncf_total_itbis'] += \
                        values['invoiced_itbis']
                    csmr_dict['csmr_ncf_total_isc'] += values['selective_tax']
                    csmr_dict['csmr_ncf_total_othr'] += values['other_taxes']
                    csmr_dict['csmr_ncf_total_lgl_tip'] += values['legal_tip']
                    csmr_dict['csmr_cash'] += values['cash']
                    csmr_dict['csmr_bank'] += values['bank']
                    csmr_dict['csmr_card'] += values['card']
                    csmr_dict['csmr_credit'] += values['credit']
                    csmr_dict['csmr_bond'] += values['bond']
                    csmr_dict['csmr_swap'] += values['swap']
                    csmr_dict['csmr_others'] += values['others']

                line += 1
                values.update({'line': line})
                SaleLine.create(values)
                if str(values.get('fiscal_invoice_number'))[-10:-8] == \
                        '02' and inv.amount_untaxed_signed < 250000:
                    excluded_line += 1
                    # Excluye las facturas de Consumo
                    # con monto menor a 250000 solo del txt
                    pass
                else:
                    report_data += self.process_607_report_data(values) + '\n'

                for k in payment_dict:
                    payment_dict[k] += payments[k] * -1 if inv.type == \
                        'out_refund' else payments[k]

            for k in op_dict:
                self.env['dgii.reports.sale.summary'].create(op_dict[k])

            self._set_csmr_fields_vals(csmr_dict)
            self._set_payment_form_fields(payment_dict)
            self._set_income_type_fields(income_dict)
            self._generate_607_txt(report_data, line - excluded_line)

    def process_608_report_data(self, values):

        NCF = str(values['fiscal_invoice_number']).ljust(11)
        INV_DATE = str(self._get_formated_date(
            values['invoice_date'])).ljust(8)
        ANU_TYPE = str(values['anulation_type']).ljust(2)

        return "|".join([NCF, INV_DATE, ANU_TYPE])

    def _generate_608_txt(self, records, qty):

        company_vat = self.company_id.vat
        period = dt.strptime(self.name.replace('/', ''),
                             '%m%Y').strftime('%Y%m')

        header = "608|{}|{}|{}".format(
            str(company_vat).ljust(11), period, qty) + '\n'
        data = header + records

        file_path = '/tmp/DGII_608_{}_{}.txt'.format(company_vat, period)
        with open(file_path, 'w', encoding="utf-8", newline='\r\n') as txt_608:
            txt_608.write(str(data))

        self.write({
            'cancel_filename': file_path.replace('/tmp/', ''),
            'cancel_binary': base64.b64encode(open(file_path, 'rb').read())
        })

    @api.multi
    def _compute_608_data(self):
        for rec in self:
            CancelLine = self.env['dgii.reports.cancel.line']
            CancelLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(['cancel'], [
                'out_invoice', 'in_invoice', 'out_refund'
            ]).filtered(lambda inv: (inv.journal_id.purchase_type != 'normal'))
            line = 0
            report_data = ''
            for inv in invoice_ids:
                inv.fiscal_status = 'blocked' if not inv.fiscal_status else \
                    inv.fiscal_status
                line += 1
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'invoice_partner_id': inv.partner_id.id,
                    'fiscal_invoice_number': inv.reference,
                    'invoice_date': inv.date_invoice,
                    'anulation_type': inv.anulation_type,
                    'invoice_id': inv.id
                }
                CancelLine.create(values)
                report_data += self.process_608_report_data(values) + '\n'

            self._generate_608_txt(report_data, line)

    def process_609_report_data(self, values):

        LEGAL_NAME = str(values['legal_name']).ljust(50)
        ID_TYPE = str(values['tax_id_type'] if values['tax_id_type'] else "")
        TAX_ID = str(values['tax_id'] if values['tax_id'] else "").ljust(50)
        CNT_CODE = str(
            values['country_code'] if values['country_code'] else "").ljust(3)
        PST = str(values['purchased_service_type']
                  if values['purchased_service_type'] else "").ljust(2)
        STD = str(values['service_type_detail']
                  if values['service_type_detail'] else "").ljust(2)
        REL_PART = str(
            values['related_part'] if values['related_part'] else "0").ljust(1)
        DOC_NUM = str(
            values['doc_number'] if values['doc_number'] else "").ljust(30)
        DOC_DATE = str(self._get_formated_date(values['doc_date'])).ljust(8)
        INV_AMOUNT = self._get_formated_amount(values['invoiced_amount'])
        ISR_DATE = str(self._get_formated_date(
            values['isr_withholding_date'])).ljust(8)
        PRM_INCM = self._get_formated_amount(values['presumed_income'])
        WH_ISR = self._get_formated_amount(values['withholded_isr'])

        return "|".join([
            LEGAL_NAME, ID_TYPE, TAX_ID, CNT_CODE, PST, STD, REL_PART, DOC_NUM,
            DOC_DATE, INV_AMOUNT, ISR_DATE, PRM_INCM, WH_ISR
        ])

    def _generate_609_txt(self, records, qty):

        company_vat = self.company_id.vat
        period = dt.strptime(self.name.replace('/', ''),
                             '%m%Y').strftime('%Y%m')

        header = "609|{}|{}|{}".format(
            str(company_vat).ljust(11), period, qty) + '\n'
        data = header + records

        file_path = '/tmp/DGII_609_{}_{}.txt'.format(company_vat, period)
        with open(file_path, 'w', encoding="utf-8", newline='\r\n') as txt_609:
            txt_609.write(str(data))

        self.write({
            'exterior_filename': file_path.replace('/tmp/', ''),
            'exterior_binary': base64.b64encode(open(file_path, 'rb').read())
        })

    @api.multi
    def _compute_609_data(self):
        for rec in self:
            ExteriorLine = self.env['dgii.reports.exterior.line']
            ExteriorLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(['open', 'in_payment', 'paid'], [
                'in_invoice', 'in_refund'
            ]).filtered(lambda inv: (inv.partner_id.country_id.code != 'DO')
                        and (inv.journal_id.purchase_type == 'exterior'))
            line = 0
            report_data = ''
            for inv in invoice_ids:
                inv.fiscal_status = 'blocked' if not inv.fiscal_status else \
                    inv.fiscal_status
                line += 1
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'legal_name': inv.partner_id.name,
                    'tax_id_type':
                        1
                        if inv.partner_id.company_type == 'individual' else 2,
                    'tax_id': inv.partner_id.vat,
                    'country_code': self._get_country_number(inv.partner_id),
                    'purchased_service_type': int(inv.service_type),
                    'service_type_detail': inv.service_type_detail.code,
                    'related_part': int(inv.partner_id.related),
                    'doc_number': inv.number,
                    'doc_date': inv.date_invoice,
                    'invoiced_amount': inv.amount_untaxed_signed,
                    'isr_withholding_date': inv.payment_date if
                    inv.payment_date else False,
                    'presumed_income': 0,  # Pendiente
                    'withholded_isr': inv.income_withholding if
                    inv.payment_date else 0,
                    'invoice_id': inv.id
                }
                ExteriorLine.create(values)
                report_data += self.process_609_report_data(values) + '\n'

            self._generate_609_txt(report_data, line)

    @api.multi
    def _generate_report(self):
        # Drop 607 NCF Operations for recompute
        self.env['dgii.reports.sale.summary'].search([('dgii_report_id', '=',
                                                       self.id)]).unlink()

        self._compute_606_data()
        self._compute_607_data()
        self._compute_608_data()
        self._compute_609_data()
        self.state = 'generated'

    @api.multi
    def generate_report(self):
        if self.state == 'generated':
            action = self.env.ref(
                'dgii_reports.dgii_report_regenerate_wizard_action').read()[0]
            action['context'] = {'default_report_id': self.id}
            return action
        else:
            self._generate_report()

    def _has_withholding(self, inv):
        """Validate if given invoice has an Withholding tax"""
        return True if any([inv.income_withholding,
                            inv.withholded_itbis,
                            inv.third_withheld_itbis,
                            inv.third_income_withholding]) else False

    @api.multi
    def _invoice_status_sent(self):
        for report in self:
            PurchaseLine = self.env['dgii.reports.purchase.line']
            SaleLine = self.env['dgii.reports.sale.line']
            CancelLine = self.env['dgii.reports.cancel.line']
            ExteriorLine = self.env['dgii.reports.exterior.line']
            invoice_ids = PurchaseLine.search([
                ('dgii_report_id', '=', report.id)
            ]).mapped('invoice_id')
            invoice_ids += SaleLine.search([
                ('dgii_report_id', '=', report.id)
            ]).mapped('invoice_id')
            invoice_ids += CancelLine.search([
                ('dgii_report_id', '=', report.id)
            ]).mapped('invoice_id')
            invoice_ids += ExteriorLine.search([
                ('dgii_report_id', '=', report.id)
            ]).mapped('invoice_id')
            for inv in invoice_ids:
                if inv.state in ['paid', 'cancel'] and \
                        self._include_in_current_report(inv):
                    inv.fiscal_status = 'done'
                    continue

                if self._has_withholding(inv):
                    inv.fiscal_status = 'normal'
                else:
                    inv.fiscal_status = 'done'

    @api.multi
    def state_sent(self):
        for report in self:
            report._invoice_status_sent()
            report.state = 'sent'

    def get_606_tree_view(self):
        return {
            'name': '606',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.purchase.line',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('dgii_reports.dgii_report_purchase_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_607_tree_view(self):
        return {
            'name': '607',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.sale.line',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('dgii_reports.dgii_report_sale_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_608_tree_view(self):
        return {
            'name': '608',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.cancel.line',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('dgii_reports.dgii_cancel_report_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_609_tree_view(self):
        return {
            'name': '609',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.exterior.line',
            'type': 'ir.actions.act_window',
            'view_id':
                self.env.ref('dgii_reports.dgii_exterior_report_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }


class DgiiReportPurchaseLine(models.Model):
    _name = 'dgii.reports.purchase.line'
    _description = "DGII Reports Purchase Line"
    _order = 'line asc'

    dgii_report_id = fields.Many2one('dgii.reports', ondelete='cascade')
    line = fields.Integer()

    rnc_cedula = fields.Char(size=11)
    identification_type = fields.Char(size=1)
    expense_type = fields.Char(size=2)
    fiscal_invoice_number = fields.Char(size=19)
    modified_invoice_number = fields.Char(size=19)
    invoice_date = fields.Date()
    payment_date = fields.Date()
    service_total_amount = fields.Float()
    good_total_amount = fields.Float()
    invoiced_amount = fields.Float()
    invoiced_itbis = fields.Float()
    withholded_itbis = fields.Float()
    proportionality_tax = fields.Float()
    cost_itbis = fields.Float()
    advance_itbis = fields.Float()
    purchase_perceived_itbis = fields.Float()
    isr_withholding_type = fields.Char()
    income_withholding = fields.Float()
    purchase_perceived_isr = fields.Float()
    selective_tax = fields.Float()
    other_taxes = fields.Float()
    legal_tip = fields.Float()
    payment_type = fields.Char()

    invoice_partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.invoice')
    credit_note = fields.Boolean()


class DgiiReportSaleLine(models.Model):
    _name = 'dgii.reports.sale.line'
    _description = "DGII Reports Sale Line"

    dgii_report_id = fields.Many2one('dgii.reports', ondelete='cascade')
    line = fields.Integer()

    rnc_cedula = fields.Char(size=11)
    identification_type = fields.Char(size=1)
    fiscal_invoice_number = fields.Char(size=19)
    modified_invoice_number = fields.Char(size=19)
    income_type = fields.Char()
    invoice_date = fields.Date()
    withholding_date = fields.Date()
    invoiced_amount = fields.Float()
    invoiced_itbis = fields.Float()
    third_withheld_itbis = fields.Float()
    perceived_itbis = fields.Float()
    third_income_withholding = fields.Float()
    perceived_isr = fields.Float()
    selective_tax = fields.Float()
    other_taxes = fields.Float()
    legal_tip = fields.Float()

    # Tipo de Venta/ Forma de pago
    cash = fields.Float()
    bank = fields.Float()
    card = fields.Float()
    credit = fields.Float()
    bond = fields.Float()
    swap = fields.Float()
    others = fields.Float()

    invoice_partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.invoice')
    credit_note = fields.Boolean()


class DgiiCancelReportLine(models.Model):
    _name = 'dgii.reports.cancel.line'
    _description = "DGII Reports Cancel Line"

    dgii_report_id = fields.Many2one('dgii.reports', ondelete='cascade')
    line = fields.Integer()

    fiscal_invoice_number = fields.Char(size=19)
    invoice_date = fields.Date()
    anulation_type = fields.Char(size=2)

    invoice_partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.invoice')


class DgiiExteriorReportLine(models.Model):
    _name = 'dgii.reports.exterior.line'
    _description = "DGII Reports Exterior Line"

    dgii_report_id = fields.Many2one('dgii.reports', ondelete='cascade')
    line = fields.Integer()

    legal_name = fields.Char()
    tax_id_type = fields.Integer()
    tax_id = fields.Char()
    country_code = fields.Char()
    purchased_service_type = fields.Char(size=2)
    service_type_detail = fields.Char(size=2)
    related_part = fields.Integer()
    doc_number = fields.Char()
    doc_date = fields.Date()
    invoiced_amount = fields.Float()
    isr_withholding_date = fields.Date()
    presumed_income = fields.Float()
    withholded_isr = fields.Float()
    invoice_id = fields.Many2one('account.invoice')
