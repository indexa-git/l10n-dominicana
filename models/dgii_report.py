# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DgiiReport(models.Model):
    _name = 'dgii.report'
    _inherit = ['mail.thread']

    name = fields.Char(string='Period', required=True, size=7)
    state = fields.Selection([('draft', 'New'), ('error', 'With error'), ('done', 'Validated')], default="draft")
    previous_balance = fields.Float("Previous balance")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id,
                                 required=True)

    # 606
    purchase_records = fields.Integer()
    service_total_amount = fields.Float()
    good_total_amount = fields.Float()
    purchase_invoiced_amount = fields.Float()
    purchase_invoiced_itbis = fields.Float()
    purchase_withholded_itbis = fields.Float()
    cost_itbis = fields.Float()
    advance_itbis = fields.Float()
    income_withholding = fields.Float()
    purchase_selective_tax = fields.Float()
    purchase_other_taxes = fields.Float()
    purchase_legal_tip = fields.Float()
    purchase_filename = fields.Char()
    purchase_binary = fields.Binary(string="606 file")

    # 607
    sale_records = fields.Integer()
    sale_invoiced_amount = fields.Float()
    sale_invoiced_itbis = fields.Float()
    sale_withholded_itbis = fields.Float()
    sale_withholded_isr = fields.Float()
    sale_selective_tax = fields.Float()
    sale_other_taxes = fields.Float()
    sale_legal_tip = fields.Float()
    sale_filename = fields.Char()
    sale_binary = fields.Binary(string="607 file")

    # 608
    cancel_records = fields.Integer()
    cancel_filename = fields.Char()
    cancel_binary = fields.Binary(string="608 file")

    # 609
    exterior_records = fields.Integer()
    presumed_income = fields.Float()
    exterior_withholded_isr = fields.Float()
    exterior_invoiced_amount = fields.Float()
    exterior_filename = fields.Char()
    exterior_binary = fields.Binary(string="609 file")

    @api.multi
    def generate_report(self):
        print("---------> Hello, world.")

    def get_606_tree_view(self):
        return {
            'name': '606',
            'view_mode': 'tree',
            'res_model': 'dgii.report.purchase.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('dgii_reports.dgii_report_purchase_line_tree').id,
            'domain': [('dgii_report_id', '=', self.id)]
        }

    def get_607_tree_view(self):
        return {
            'name': '607',
            'view_mode': 'tree',
            'res_model': 'dgii.report.sale.line',
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
    _name = "dgii.report.purchase.line"

    dgii_report_id = fields.Many2one("dgii.report")
    line = fields.Integer()
    rnc_cedula = fields.Char(size=11)
    identification_type = fields.Char(size=1)
    fiscal_invoice_number = fields.Char(size=19)
    modified_invoice_number = fields.Char(size=19)
    invoice_date = fields.Date()
    payment_date = fields.Date()
    expense_type = fields.Char(size=2)
    invoiced_itbis = fields.Float()
    withholded_itbis = fields.Float()
    invoiced_amount = fields.Float()
    income_withholding = fields.Float()
    invoice = fields.Many2one("account.invoice")
    number = fields.Char(related="invoice.number")
    invoice_partner_id = fields.Many2one("res.partner", related="invoice.partner_id")
    affected_invoice_id = fields.Many2one("account.invoice")
    credit_note = fields.Boolean()


class DgiiReportSaleLine(models.Model):
    _name = "dgii.report.sale.line"

    dgii_report_id = fields.Many2one("dgii.report")
    line = fields.Integer()
    rnc_cedula = fields.Char(size=11)
    identification_type = fields.Char(size=1)
    fiscal_invoice_number = fields.Char(size=19)
    modified_invoice_number = fields.Char(size=19)
    income_type = fields.Char()
    invoice_date = fields.Date()
    payment_date = fields.Date()
    invoiced_itbis = fields.Float()
    invoiced_amount = fields.Float()
    invoice = fields.Many2one("account.invoice")
    number = fields.Char(related="invoice.number")
    invoice_partner_id = fields.Many2one("res.partner", related="invoice.partner_id")
    affected_invoice_id = fields.Many2one("account.invoice")
    credit_note = fields.Boolean()


class DgiiCancelReportline(models.Model):
    _name = "dgii.cancel.report.line"

    dgii_report_id = fields.Many2one("dgii.report")
    line = fields.Integer()
    fiscal_invoice_number = fields.Char(size=19)
    invoice_date = fields.Date()
    anulation_type = fields.Char(size=2)
    invoice = fields.Many2one("account.invoice")


class DgiiExteriorReportline(models.Model):
    _name = "dgii.exterior.report.line"

    dgii_report_id = fields.Many2one("dgii.report")
    line = fields.Integer()
    expense_type = fields.Char(size=2)
    invoice_date = fields.Date()
    payment_date = fields.Date()
    income_withholding = fields.Float()
    invoiced_amount = fields.Float()
    invoice = fields.Many2one("account.invoice")
