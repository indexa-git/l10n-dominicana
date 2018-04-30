# -*- coding: utf-8 -*-

import calendar
from datetime import datetime as dt

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DgiiReportSaleSummary(models.Model):
    _name = 'dgii.reports.sale.summary'
    _order = 'sequence'

    name = fields.Char()
    sequence = fields.Integer()
    qty = fields.Integer()
    amount = fields.Monetary()
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    dgii_report_id = fields.Many2one('dgii.reports', ondelete='cascade')


class DgiiReport(models.Model):
    _name = 'dgii.reports'
    _inherit = ['mail.thread']

    name = fields.Char(string='Period', required=True, size=7)
    state = fields.Selection([('draft', 'New'), ('error', 'With error'),
                              ('generated', 'Generated'), ('sent', 'Sent')],
                             default='draft', track_visibility='onchange', copy=False)
    previous_balance = fields.Float('Previous balance', copy=False)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id,
                                 required=True)

    @api.multi
    def _compute_606_fields(self):
        for rec in self:
            purchase_line_ids = self.env['dgii.reports.purchase.line'].search([('dgii_report_id', '=', rec.id)])
            rec.purchase_records = len(purchase_line_ids)
            rec.service_total_amount = abs(sum([inv.service_total_amount for inv in purchase_line_ids]))
            rec.good_total_amount = abs(sum([inv.good_total_amount for inv in purchase_line_ids]))
            rec.purchase_invoiced_amount = abs(sum([inv.invoiced_amount for inv in purchase_line_ids]))
            rec.purchase_invoiced_itbis = abs(sum([inv.invoiced_itbis for inv in purchase_line_ids]))
            rec.purchase_withholded_itbis = abs(sum([inv.withholded_itbis for inv in purchase_line_ids]))
            rec.cost_itbis = abs(sum([inv.cost_itbis for inv in purchase_line_ids]))
            rec.advance_itbis = abs(sum([inv.advance_itbis for inv in purchase_line_ids]))
            rec.income_withholding = abs(sum([inv.income_withholding for inv in purchase_line_ids]))
            rec.purchase_selective_tax = abs(sum([inv.selective_tax for inv in purchase_line_ids]))
            rec.purchase_other_taxes = abs(sum([inv.other_taxes for inv in purchase_line_ids]))
            rec.purchase_legal_tip = abs(sum([inv.legal_tip for inv in purchase_line_ids]))

    @api.multi
    def _compute_607_fields(self):
        for rec in self:
            sale_line_ids = self.env['dgii.reports.sale.line'].search([('dgii_report_id', '=', rec.id)])
            rec.sale_records = len(sale_line_ids)
            rec.sale_invoiced_amount = abs(sum([inv.invoiced_amount for inv in sale_line_ids]))
            rec.sale_invoiced_itbis = abs(sum([inv.invoiced_itbis for inv in sale_line_ids]))
            rec.sale_withholded_itbis = abs(sum([inv.third_withheld_itbis for inv in sale_line_ids]))
            rec.sale_withholded_isr = abs(sum([inv.third_income_withholding for inv in sale_line_ids]))
            rec.sale_selective_tax = abs(sum([inv.selective_tax for inv in sale_line_ids]))
            rec.sale_other_taxes = abs(sum([inv.other_taxes for inv in sale_line_ids]))
            rec.sale_legal_tip = abs(sum([inv.legal_tip for inv in sale_line_ids]))

    @api.multi
    def _compute_608_fields(self):
        for rec in self:
            cancel_line_ids = self.env['dgii.reports.cancel.line'].search([('dgii_report_id', '=', rec.id)])
            rec.cancel_records = len(cancel_line_ids)

    @api.multi
    def _compute_609_fields(self):
        for rec in self:
            external_line_ids = self.env['dgii.reports.exterior.line'].search([('dgii_report_id', '=', rec.id)])
            rec.exterior_records = len(external_line_ids)
            rec.presumed_income = abs(sum([inv.presumed_income for inv in external_line_ids]))
            rec.exterior_withholded_isr = abs(sum([inv.withholded_isr for inv in external_line_ids]))
            rec.exterior_invoiced_amount = abs(sum([inv.invoiced_amount for inv in external_line_ids]))

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

    # Additional Info
    ncf_sale_summary_ids = fields.One2many('dgii.reports.sale.summary', 'dgii_report_id',
                                           string='Operations by NCF type', copy=False)
    cash = fields.Monetary('Cash', copy=False)
    bank = fields.Monetary('Check / Transfer / Deposit', copy=False)
    card = fields.Monetary('Credit Card / Debit Card', copy=False)
    credit = fields.Monetary('Credit', copy=False)
    bond = fields.Monetary('Gift certificates or vouchers', copy=False)
    swap = fields.Monetary('Swap', copy=False)
    others = fields.Monetary('Other Sale Forms', copy=False)
    sale_type_total = fields.Monetary('Total', copy=False)

    opr_income = fields.Monetary('Operations Income (No-Financial)', copy=False)
    fin_income = fields.Monetary('Financial Income', copy=False)
    ext_income = fields.Monetary('Extraordinary Income', copy=False)
    lea_income = fields.Monetary('Lease Income', copy=False)
    ast_income = fields.Monetary('Depreciable Assets Income', copy=False)
    otr_income = fields.Monetary('Others Income', copy=False)
    income_type_total = fields.Monetary('Total', copy=False)

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

    @api.multi
    def unlink(self):
        """When report is deleted, set all implied invoices fiscal_status to False"""
        for report in self:
            PurchaseLine = self.env['dgii.reports.purchase.line']
            SaleLine = self.env['dgii.reports.sale.line']
            CancelLine = self.env['dgii.reports.cancel.line']
            ExteriorLine = self.env['dgii.reports.exterior.line']
            invoice_ids = PurchaseLine.search([('dgii_report_id', '=', report.id)]).mapped('invoice_id')
            invoice_ids += SaleLine.search([('dgii_report_id', '=', report.id)]).mapped('invoice_id')
            invoice_ids += CancelLine.search([('dgii_report_id', '=', report.id)]).mapped('invoice_id')
            invoice_ids += ExteriorLine.search([('dgii_report_id', '=', report.id)]).mapped('invoice_id')
            for inv in invoice_ids:
                inv.fiscal_status = False
        return super(DgiiReport, self).unlink()

    def _get_pending_invoices(self):
        return self.env['account.invoice'].search([('fiscal_status', '=', 'normal'), ('state', '=', 'paid')])

    def _get_invoices(self, rec, states, types):
        """
        Given rec and state, return a recordset of invoices
        :param rec: dgii.reports object
        :param state: a list of invoice state
        :param type: a list of invoice type
        :return: filtered invoices
        """
        month, year = rec.name.split('/')
        last_day = calendar.monthrange(int(year), int(month))[1]
        start_date = '{}-{}-01'.format(year, month)
        end_date = '{}-{}-{}'.format(year, month, last_day)

        invoice_ids = self.env['account.invoice'].search(
            [('date_invoice', '>=', start_date),
             ('date_invoice', '<=', end_date),
             ('company_id', '=', self.company_id.id),
             ('state', 'in', states),
             ('type', 'in', types)],
            order='date_invoice asc').filtered(lambda inv: (inv.journal_id.purchase_type != 'others') or
                                                           (inv.journal_id.ncf_control is True))

        # Append pending invoces (fiscal_status = Partial, state = Paid)
        invoice_ids += self._get_pending_invoices()

        return invoice_ids

    def formated_rnc_cedula(self, vat):
        if vat:
            if len(vat) in [9, 11]:
                id_type = 1 if len(vat) == 9 else 2
                return (vat.strip().replace('-', ''), id_type) if not vat.isspace() else False
            else:
                return False
        else:
            return False

    @api.multi
    def _compute_606_data(self):
        for rec in self:
            PurchaseLine = self.env['dgii.reports.purchase.line']
            PurchaseLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(rec, ['open', 'paid'], ['in_invoice', 'in_refund'])

            line = 0
            for inv in invoice_ids:
                inv.fiscal_status = 'blocked'
                line += 1
                rnc_ced = self.formated_rnc_cedula(inv.partner_id.vat)
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'rnc_cedula': rnc_ced[0] if rnc_ced else False,
                    'identification_type': rnc_ced[1] if rnc_ced else False,
                    'expense_type': inv.expense_type if inv.expense_type else False,
                    'fiscal_invoice_number': inv.move_name,
                    'modified_invoice_number': inv.origin,
                    'invoice_date': inv.date_invoice,
                    'payment_date': inv.payment_date,
                    'service_total_amount': inv.service_total_amount,
                    'good_total_amount': inv.good_total_amount,
                    'invoiced_amount': inv.amount_untaxed_signed,
                    'invoiced_itbis': inv.invoiced_itbis,
                    'proportionality_tax': inv.proportionality_tax,
                    'cost_itbis': inv.cost_itbis,
                    'advance_itbis': inv.advance_itbis,
                    'purchase_perceived_itbis': 0,  # Falta computarlo en la factura
                    'purchase_perceived_isr': 0,  # Falta computarlo en la factura
                    'isr_withholding_type': inv.isr_withholding_type,
                    'withholded_itbis': inv.withholded_itbis if inv.state == 'paid' else 0,
                    'income_withholding': inv.income_withholding if inv.state == 'paid' else 0,
                    'selective_tax': inv.selective_tax,
                    'other_taxes': inv.other_taxes,
                    'legal_tip': inv.legal_tip,
                    'payment_type': inv.payment_form,
                    'invoice_partner_id': inv.partner_id.id,
                    'invoice_id': inv.id,
                    'credit_note': True if inv.type == 'in_refund' else False
                }
                PurchaseLine.create(values)

    def _get_payments_dict(self):
        return {'cash': 0, 'bank': 0, 'card': 0, 'credit': 0, 'swap': 0, 'bond': 0, 'others': 0}

    def _convert_to_user_currency(self, base_currency, amount):
        context = dict(self._context or {})
        user_currency_id = self.env.user.company_id.currency_id
        base_currency_id = base_currency
        ctx = context.copy()
        return base_currency_id.with_context(ctx).compute(amount, user_currency_id)

    def _get_sale_payments_forms(self, invoice_id):
        payments_dict = self._get_payments_dict()
        for move_line in invoice_id.payment_move_line_ids:
            key = move_line.journal_id.payment_form
            if key:
                payments_dict[key] += move_line.credit

        payments_dict['credit'] += self._convert_to_user_currency(invoice_id.currency_id, invoice_id.residual)
        return payments_dict

    def _get_607_operations_dict(self):
        return {
            'fiscal': {'sequence': 1, 'qty': 0, 'amount': 0, 'name': 'COMPROBANTE VÁLIDO PARA CRÉDITO FISCAL',
                       'dgii_report_id': self.id},
            'final': {'sequence': 2, 'qty': 0, 'amount': 0, 'name': 'COMPROBANTE CONSUMIDOR FINAL',
                      'dgii_report_id': self.id},
            'nd': {'sequence': 3, 'qty': 0, 'amount': 0, 'name': 'COMPROBANTES NOTA DE DÉBITO',
                   'dgii_report_id': self.id},
            'nc': {'sequence': 4, 'qty': 0, 'amount': 0, 'name': 'COMPROBANTES NOTA DE CRÉDITO',
                   'dgii_report_id': self.id},
            'unico': {'sequence': 5, 'qty': 0, 'amount': 0, 'name': 'COMPROBANTE REGISTRO ÚNICO DE INGRESOS',
                      'dgii_report_id': self.id},
            'special': {'sequence': 6, 'qty': 0, 'amount': 0, 'name': 'COMPROBANTE REGISTRO REGIMENES ESPECIALES',
                        'dgii_report_id': self.id},
            'gov': {'sequence': 7, 'qty': 0, 'amount': 0, 'name': 'COMPROBANTES GUBERNAMENTALES',
                    'dgii_report_id': self.id},
            'positive': {'sequence': 8, 'qty': 0, 'amount': 0, 'name': 'OTRAS OPERACIONES (POSITIVAS) - *PENDIENTE*',
                         'dgii_report_id': self.id},
            'negative': {'sequence': 9, 'qty': 0, 'amount': 0, 'name': 'OTRAS OPERACIONES (NEGATIVAS) - *PENDIENTE*',
                         'dgii_report_id': self.id},
        }

    def _process_op_dict(self, dict, invoice):
        op_dict = dict
        if invoice.sale_fiscal_type and invoice.type != 'out_refund':
            op_dict[invoice.sale_fiscal_type]['qty'] += 1
            op_dict[invoice.sale_fiscal_type]['amount'] += invoice.amount_untaxed_signed
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
                                  rec.card + rec.credit + \
                                  rec.bond + rec.swap + rec.others

    def _get_income_type_dict(self):
        return {'01': 0, '02': 0, '03': 0, '04': 0, '05': 0, '06': 0}

    def _process_income_dict(self, dict, invoice):
        income_dict = dict
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
            rec.income_type_total = rec.opr_income + rec.fin_income + rec.ext_income + \
                                    rec.lea_income + rec.ast_income + rec.otr_income

    @api.multi
    def _compute_607_data(self):
        for rec in self:
            SaleLine = self.env['dgii.reports.sale.line']
            SaleLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(rec, ['open', 'paid'], ['out_invoice', 'out_refund'])
            line = 0
            op_dict = self._get_607_operations_dict()
            payment_dict = self._get_payments_dict()
            income_dict = self._get_income_type_dict()
            for inv in invoice_ids:
                op_dict = self._process_op_dict(op_dict, inv)
                income_dict = self._process_income_dict(income_dict, inv)
                inv.fiscal_status = 'blocked'
                line += 1
                rnc_ced = self.formated_rnc_cedula(inv.partner_id.vat)
                payments = self._get_sale_payments_forms(inv)
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'rnc_cedula': rnc_ced[0] if rnc_ced else False,
                    'identification_type': rnc_ced[1] if rnc_ced else False,
                    'fiscal_invoice_number': inv.move_name,
                    'modified_invoice_number': inv.origin if inv.type == 'out_refund' else False,
                    'income_type': inv.income_type,
                    'invoice_date': inv.date_invoice,
                    'withholding_date': inv.payment_date,
                    'invoiced_amount': inv.amount_untaxed_signed,
                    'invoiced_itbis': inv.invoiced_itbis,
                    'third_withheld_itbis': inv.third_withheld_itbis if inv.state == 'paid' else 0,
                    'perceived_itbis': 0,  # Pendiente
                    'third_income_withholding': inv.third_income_withholding if inv.state == 'paid' else 0,
                    'perceived_isr': 0,  # Pendiente
                    'selective_tax': inv.selective_tax,
                    'other_taxes': inv.other_taxes,
                    'legal_tip': inv.legal_tip,
                    'invoice_partner_id': inv.partner_id.id,
                    'invoice_id': inv.id,
                    'credit_note': True if inv.type == 'out_refund' else False,
                    'cash': payments.get('cash'),
                    'bank': payments.get('bank'),
                    'card': payments.get('card'),
                    'credit': payments.get('credit'),
                    'swap': payments.get('swap'),
                    'bond': payments.get('bond'),
                    'others': payments.get('others')
                }
                SaleLine.create(values)

                for k in payment_dict:
                    if inv.type != 'out_refund':
                        payment_dict[k] += payments[k]

            for k in op_dict:
                self.env['dgii.reports.sale.summary'].create(op_dict[k])

            self._set_payment_form_fields(payment_dict)
            self._set_income_type_fields(income_dict)

    @api.multi
    def _compute_608_data(self):
        for rec in self:
            CancelLine = self.env['dgii.reports.cancel.line']
            CancelLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(rec, ['cancel'], ['out_invoice', 'out_refund'])
            line = 0
            for inv in invoice_ids:
                inv.fiscal_status = 'blocked'
                line += 1
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'invoice_partner_id': inv.partner_id.id,
                    'fiscal_invoice_number': inv.move_name,
                    'invoice_date': inv.date_invoice,
                    'anulation_type': inv.anulation_type,
                    'invoice_id': inv.id
                }
                CancelLine.create(values)

    @api.multi
    def _compute_609_data(self):
        for rec in self:
            ExteriorLine = self.env['dgii.reports.exterior.line']
            ExteriorLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(rec,
                                             ['open', 'paid'],
                                             ['in_invoice',
                                              'in_refund']
                                             ).filtered(lambda inv: (inv.partner_id.country_id.code != 'DO') and
                                                                    (inv.journal_id.purchase_type == 'exterior'))
            line = 0
            for inv in invoice_ids:
                inv.fiscal_status = 'blocked'
                line += 1
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'legal_name': inv.partner_id.name,
                    'tax_id_type': 1 if inv.partner_id.company_type == 'individual' else 2,
                    'tax_id': inv.partner_id.vat,
                    'country_code': inv.partner_id.country_id.code,
                    'purchased_service_type': inv.service_type,
                    'service_type_detail': inv.service_type_detail.code,
                    'related_part': int(inv.partner_id.related),
                    'doc_number': inv.number,
                    'doc_date': inv.date_invoice,
                    'invoiced_amount': inv.amount_untaxed_signed,
                    'isr_withholding_date': inv.payment_date,
                    'presumed_income': 0,  # Pendiente
                    'withholded_isr': inv.income_withholding if inv.state == 'paid' else 0,
                    'invoice_id': inv.id
                }
                ExteriorLine.create(values)

    @api.multi
    def generate_report(self):
        # Drop 607 NCF Operations for recompute
        self.env['dgii.reports.sale.summary'].search([('dgii_report_id', '=', self.id)]).unlink()

        self._compute_606_data()
        self._compute_607_data()
        self._compute_608_data()
        self._compute_609_data()
        self.state = 'generated'

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
            invoice_ids = PurchaseLine.search([('dgii_report_id', '=', report.id)]).mapped('invoice_id')
            invoice_ids += SaleLine.search([('dgii_report_id', '=', report.id)]).mapped('invoice_id')
            invoice_ids += CancelLine.search([('dgii_report_id', '=', report.id)]).mapped('invoice_id')
            invoice_ids += ExteriorLine.search([('dgii_report_id', '=', report.id)]).mapped('invoice_id')
            for inv in invoice_ids:
                if inv.state in ['paid', 'cancel']:
                    inv.fiscal_status = 'done'
                    continue

                if self._has_withholding(inv):
                    inv.fiscal_status = 'normal'
                else:
                    inv.fiscal_status = 'done'

    @api.multi
    def state_sent(self):
        for report in self:
            self._invoice_status_sent()
            report.state = 'sent'

    def get_606_tree_view(self):
        return {
            'name': '606',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.purchase.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('dgii_reports.dgii_report_purchase_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_607_tree_view(self):
        return {
            'name': '607',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.sale.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('dgii_reports.dgii_report_sale_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_608_tree_view(self):
        return {
            'name': '608',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.cancel.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('dgii_reports.dgii_cancel_report_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_609_tree_view(self):
        return {
            'name': '609',
            'view_mode': 'tree',
            'res_model': 'dgii.reports.exterior.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('dgii_reports.dgii_exterior_report_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }


class DgiiReportPurchaseLine(models.Model):
    _name = 'dgii.reports.purchase.line'
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

    dgii_report_id = fields.Many2one('dgii.reports', ondelete='cascade')
    line = fields.Integer()

    fiscal_invoice_number = fields.Char(size=19)
    invoice_date = fields.Date()
    anulation_type = fields.Char(size=2)

    invoice_partner_id = fields.Many2one('res.partner')
    invoice_id = fields.Many2one('account.invoice')


class DgiiExteriorReportLine(models.Model):
    _name = 'dgii.reports.exterior.line'

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
