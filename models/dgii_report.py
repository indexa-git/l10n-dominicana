# -*- coding: utf-8 -*-

import calendar
from datetime import datetime as dt

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DgiiReport(models.Model):
    _name = 'dgii.reports'
    _inherit = ['mail.thread']

    name = fields.Char(string='Period', required=True, size=7)
    state = fields.Selection([('draft', 'New'), ('error', 'With error'), ('done', 'Validated')], default='draft')
    previous_balance = fields.Float('Previous balance')
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
            cancel_line_ids = self.env['dgii.cancel.report.line'].search([('dgii_report_id', '=', rec.id)])
            rec.cancel_records = len(cancel_line_ids)

    @api.multi
    def _compute_609_fields(self):
        for rec in self:
            external_line_ids = self.env['dgii.exterior.report.line'].search([('dgii_report_id', '=', rec.id)])
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

    def _get_invoices(self, rec, states, types, ):
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
                    'withholded_itbis': inv.withholded_itbis,
                    'proportionality_tax': inv.proportionality_tax,
                    'cost_itbis': inv.cost_itbis,
                    'advance_itbis': inv.advance_itbis,
                    'purchase_perceived_itbis': 0,  # Falta computarlo en la factura
                    'isr_withholding_type': inv.isr_withholding_type,
                    'income_withholding': inv.income_withholding,
                    'purchase_perceived_isr': 0,  # Falta computarlo en la factura
                    'selective_tax': inv.selective_tax,
                    'other_taxes': inv.other_taxes,
                    'legal_tip': inv.legal_tip,
                    'payment_type': inv.payment_form,
                    'invoice_partner_id': inv.partner_id.id,
                    'credit_note': True if inv.type == 'in_refund' else False
                }
                PurchaseLine.create(values)

    def _get_sale_payments_forms(self, invoice_id):
        payments_dict = {'cash': 0, 'bank': 0, 'card': 0, 'credit': 0, 'swap': 0, 'bond': 0, 'others': 0}
        for move_line in invoice_id.payment_move_line_ids:
            key = move_line.journal_id.payment_form
            if key:
                payments_dict[key] += move_line.credit

        return payments_dict

    @api.multi
    def _compute_607_data(self):
        for rec in self:
            SaleLine = self.env['dgii.reports.sale.line']
            SaleLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(rec, ['open', 'paid'], ['out_invoice', 'out_refund'])
            line = 0
            for inv in invoice_ids:
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
                    'withholding_date': False,  # Pendiente
                    'invoiced_amount': inv.amount_untaxed_signed,
                    'invoiced_itbis': inv.invoiced_itbis,
                    'third_withheld_itbis': inv.third_withheld_itbis,
                    'perceived_itbis': 0,  # Pendiente
                    'third_income_withholding': inv.third_income_withholding,
                    'perceived_isr': 0,  # Pendiente
                    'selective_tax': inv.selective_tax,
                    'other_taxes': inv.other_taxes,
                    'legal_tip': inv.legal_tip,
                    'invoice_partner_id': inv.partner_id.id,
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

    @api.multi
    def _compute_608_data(self):
        for rec in self:
            CancelLine = self.env['dgii.cancel.report.line']
            CancelLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(rec, ['cancel'], ['out_invoice', 'out_refund'])
            line = 0
            for inv in invoice_ids:
                line += 1
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'invoice_partner_id': inv.partner_id.id,
                    'fiscal_invoice_number': inv.move_name,
                    'invoice_date': inv.date_invoice,
                    'anulation_type': inv.anulation_type,
                }
                CancelLine.create(values)

    @api.multi
    def _compute_609_data(self):
        for rec in self:
            ExteriorLine = self.env['dgii.exterior.report.line']
            ExteriorLine.search([('dgii_report_id', '=', rec.id)]).unlink()

            invoice_ids = self._get_invoices(rec, ['open', 'paid'], ['in_invoice', 'in_refund'])
            line = 0
            for inv in invoice_ids:
                line += 1
                values = {
                    'dgii_report_id': rec.id,
                    'line': line,
                    'legal_name': inv.partner_id.name,
                    'tax_id_type': 1 if inv.partner_id.company_type == 'individual' else 2,
                    'tax_id': inv.partner_id.vat,
                    'country_code': inv.partner_id.country_id.code,
                    'purchased_service_type': inv.service_type,
                    'service_type_detail': inv.service_type_detail,
                    'related_part': int(inv.partner_id.related),
                    'doc_number': inv.number,
                    'doc_date': inv.date_invoice,
                    'invoiced_amount': inv.amount_untaxed_signed,
                    'isr_withholding_date': False,
                    'presumed_income': 0,  # Pendiente
                    'withholded_isr': inv.income_withholding,
                }
                ExteriorLine.create(values)

    @api.multi
    def generate_report(self):
        self._compute_606_data()
        self._compute_607_data()
        self._compute_608_data()
        self._compute_609_data()

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
            'res_model': 'dgii.cancel.report.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('dgii_reports.dgii_cancel_report_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_609_tree_view(self):
        return {
            'name': '609',
            'view_mode': 'tree',
            'res_model': 'dgii.exterior.report.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('dgii_reports.dgii_exterior_report_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }


class DgiiReportPurchaseLine(models.Model):
    _name = 'dgii.reports.purchase.line'
    _order = 'line asc'

    dgii_report_id = fields.Many2one('dgii.reports')
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
    credit_note = fields.Boolean()


class DgiiReportSaleLine(models.Model):
    _name = 'dgii.reports.sale.line'

    dgii_report_id = fields.Many2one('dgii.reports')
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
    credit_note = fields.Boolean()


class DgiiCancelReportline(models.Model):
    _name = 'dgii.cancel.report.line'

    dgii_report_id = fields.Many2one('dgii.reports')
    line = fields.Integer()

    fiscal_invoice_number = fields.Char(size=19)
    invoice_date = fields.Date()
    anulation_type = fields.Char(size=2)

    invoice_partner_id = fields.Many2one('res.partner')


class DgiiExteriorReportline(models.Model):
    _name = 'dgii.exterior.report.line'

    dgii_report_id = fields.Many2one('dgii.reports')
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
