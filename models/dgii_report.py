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
    
    rnc_cedula = fields.Char(size=11)               # RNC o Cédula
    identification_type = fields.Char(size=1)       # Tipo Id
    expense_type = fields.Char(size=2)              # Tipo Bienes y Servicios Comprados
    fiscal_invoice_number = fields.Char(size=19)    # NCF
    modified_invoice_number = fields.Char(size=19)  # NCF o Documento Modificado
    invoice_date = fields.Date()                    # Fecha Comprobante
    payment_date = fields.Date()                    # Fecha Pago
    service_total_amount = fields.Float()           # Monto Facturado en Servicios
    good_total_amount = fields.Float()              # Monto Facturado en Bienes
    invoiced_amount = fields.Float()                # Total Monto Facturado
    invoiced_itbis = fields.Float()                 # ITBIS Facturado
    withholded_itbis = fields.Float()               # ITBIS Retenido
    proportionality_tax = fields.Float()            # ITBIS sujeto a Proporcionalidad
    cost_itbis = fields.Float()                     # ITBIS llevado al Costo
    advance_itbis = fields.Float()                  # ITBIS por Adelantar
    purchase_perceived_itbis = fields.Float()       # ITBIS percibido en compras
    isr_withholding_type = fields.Char()            # Tipo de Retención en ISR
    income_withholding = fields.Float()             # Monto Retención Renta
    purchase_perceived_isr = fields.Float()         # ISR Percibido en compras
    excise_tax = fields.Float()                     # Impuesto Selectivo al Consumo
    other_taxes = fields.Float()                    # Otros Impuestos/Tasas
    legal_tip = fields.Float()                      # Monto Propina Legal
    payment_type = fields.Char()                    # Forma de Pago

    # Los siguientes campos no estan en la Norma. Validar si van o no.
    invoice = fields.Many2one("account.invoice")
    invoice_partner_id = fields.Many2one("res.partner", related="invoice.partner_id")
    credit_note = fields.Boolean()


class DgiiReportSaleLine(models.Model):
    _name = "dgii.report.sale.line"

    dgii_report_id = fields.Many2one("dgii.report")
    line = fields.Integer()

    rnc_cedula = fields.Char(size=11)               # RNC, Cédula o Pasaporte
    identification_type = fields.Char(size=1)       # Tipo Identificación
    fiscal_invoice_number = fields.Char(size=19)    # Número Comprobante Fiscal
    modified_invoice_number = fields.Char(size=19)  # Numero Comprobante Modificado
    income_type = fields.Char()                     # Tipo de Ingreso
    invoice_date = fields.Date()                    # Fecha Comprobante
    withholding_date = fields.Date()                # Fecha de Retención
    invoiced_amount = fields.Float()                # Monto Facturado
    invoiced_itbis = fields.Float()                 # ITBIS Facturado
    third_withheld_itbis = fields.Float()           # ITBIS Retenido por Terceros
    perceived_itbis = fields.Float()                # ITBIS Percibido
    third_income_withholding = fields.Float()       # Retención de Renta por Terceros
    perceived_isr = fields.Float()                  # ISR Percibido
    excise_tax = fields.Float()                     # Impuesto Selectivo al Consumo
    other_taxes = fields.Float()                    # Otros Impuestos/Tasas
    legal_tip = fields.Float()                      # Monto Propina Legal

    # Tipo de Venta/ Forma de pago
    cash = fields.Float()                           # Efectivo
    check_transfer_deposit = fields.Float()         # Cheque/ Transferencia/ Depósito
    debit_credit_card = fields.Float()              # Tarjeta Débito/ Crédito
    credit_sale = fields.Float()                    # Venta a Crédito
    bonus_gift_certificates = fields.Float()        # Bonos o Certificados de Regalo
    barter = fields.Float()                         # Permuta
    other_sale_form = fields.Float()                # Otras Formas de Ventas

    # Los siguientes campos no estan en la Norma. Validar si van o no.
    invoice = fields.Many2one("account.invoice")
    invoice_partner_id = fields.Many2one("res.partner", related="invoice.partner_id")
    credit_note = fields.Boolean()


class DgiiCancelReportline(models.Model):
    _name = "dgii.cancel.report.line"

    dgii_report_id = fields.Many2one("dgii.report")
    line = fields.Integer()

    fiscal_invoice_number = fields.Char(size=19)    # Numero Comprobante Fiscal
    invoice_date = fields.Date()                    # Fecha Comprobante
    anulation_type = fields.Char(size=2)            # Tipo Anulación

    # Los siguientes campos no estan en la Norma. Validar si van o no.
    invoice = fields.Many2one("account.invoice")


class DgiiExteriorReportline(models.Model):
    _name = "dgii.exterior.report.line"

    dgii_report_id = fields.Many2one("dgii.report")
    line = fields.Integer()

    legal_name = fields.Char()                      # Razón Social
    tax_id_type = fields.Char()                     # Tipo Id Tributaria
    tax_id = fields.Char()                          # Id tributaria
    country_code = fields.Char()                    # País destino
    purchased_service_type = fields.Char()          # Tipo servicios adquirido
    service_type_detail = fields.Char()             # Detalles del Servicio Adquirido
    related_part = fields.Char()                    # Parte relacionada
    doc_number = fields.Char()                      # Numero de documento
    doc_date = fields.Date()                        # Fecha documento
    invoiced_amount = fields.Float()                # Monto facturado
    isr_withholding_date = fields.Date()            # Fecha Retención ISR
    presumed_income = fields.Float()                # Renta Presunta
    withholded_isr = fields.Float()                 # ISR retenido

    # Los siguientes campos no estan en la Norma. Validar si van o no.
    expense_type = fields.Char(size=2)
    invoice_date = fields.Date()
    payment_date = fields.Date()
    income_withholding = fields.Float()
    invoice = fields.Many2one("account.invoice")
