# -*- coding: utf-8 -*-

import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountInvoiceDgiiTaxes(models.Model):
    _name = 'account.invoice.payment'

    name = fields.Char()
    amount = fields.Monetary()
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    currency_id = fields.Many2one('res.currency', string='Currency', related='invoice_id.currency_id')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.constrains('tax_line_ids')
    def _check_isr_tax(self):
        """Restrict one ISR tax per invoice"""
        for inv in self:
            l = [tax_line.tax_id.purchase_tax_type for tax_line in inv.tax_line_ids
                 if tax_line.tax_id.purchase_tax_type in ['isr', 'ritbis']]
            if len(l) != len(set(l)):
                raise ValidationError(_('An invoice cannot have multiple withholding taxes.'))

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.amount', 'state')
    def _compute_taxes_fields(self):
        for inv in self:
            if inv.type == 'in_invoice' and inv.state != 'draft':
                # Monto ITBIS Retenido
                inv.withholded_itbis = abs(sum([tax.amount for tax in inv.tax_line_ids
                                                if tax.tax_id.purchase_tax_type == 'ritbis']))

                # Monto Retención Renta
                inv.income_withholding = abs(sum([tax.amount for tax in inv.tax_line_ids
                                                  if tax.tax_id.purchase_tax_type == 'isr']))

                # Monto Impuesto Selectivo al Consumo
                inv.selective_tax = abs(sum([tax.amount for tax in inv.tax_line_ids
                                             if tax.tax_id.tax_group_id.name == 'ISC']))

                # Monto Otros Impuestos/Tasas
                inv.other_taxes = abs(sum([tax.amount for tax in inv.tax_line_ids
                                           if tax.tax_id.purchase_tax_type not in ['isr', 'ritbis']
                                           and tax.tax_id.tax_group_id.name[:5] not in ['ISC', 'ITBIS']]))

                # Monto Propina Legal
                inv.legal_tip = abs(sum([tax.amount for tax in inv.tax_line_ids
                                         if tax.tax_id.tax_group_id.name == 'Propina Legal (10%)']))

            elif inv.type == 'out_invoice':
                # TODO: Implement taxes fields compute when invoice is out_invoice
                pass

    @api.multi
    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'state')
    def _compute_amount_fields(self):
        for inv in self:
            if inv.type == 'in_invoice' and inv.state != 'draft':
                # Monto calculado en servicio
                inv.service_total_amount = sum([line.price_subtotal for line in inv.invoice_line_ids
                                                if line.product_id.type == 'service'])

                # Monto calculado en bienes
                inv.good_total_amount = sum([line.price_subtotal for line in inv.invoice_line_ids
                                             if line.product_id.type != 'service'])
            elif inv.type == 'out_invoice':
                # TODO: Implement amount fields compute when invoice is out_invoice
                pass

    @api.multi
    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'state')
    def _compute_isr_withholding_type(self):
        for inv in self:
            if inv.type == 'in_invoice' and inv.state != 'draft':
                isr = [tax_line.tax_id for tax_line in inv.tax_line_ids if tax_line.tax_id.purchase_tax_type == 'isr']
                if isr:
                    inv.isr_withholding_type = isr.pop(0).isr_retention_type

    def _get_payment_string(self, invoice_id):
        """Compute Vendor Bills payment method string"""
        payments = []
        p_string = ""
        j = json.loads(invoice_id.payments_widget)

        for payment in j['content']:
            payment_id = self.env['account.payment'].browse(payment.get('account_payment_id'))
            if payment_id:
                if payment_id.journal_id.type in ['cash', 'bank']:
                    p_string = payment_id.journal_id.payment_form

            # If invoice is paid, but the payment doesn't come from
            # a journal, assume it is a credit note
            payment = p_string if payment_id else 'credit_note'
            payments.append(payment)

        if payments:
            methods = {p for p in payments}
            if len(methods) == 1:
                return list(methods)[0]
            elif len(methods) > 1:
                return 'mixed'

    @api.multi
    @api.depends('state')
    def _compute_payment_form(self):
        for inv in self:
            if inv.type == 'in_invoice' and inv.state == 'paid':
                payment_dict = {'cash': '01', 'bank': '02', 'card': '03', 'credit': '04', 'swap': '05',
                                'credit_note': '06', 'mixed': '07'}
                inv.payment_form = payment_dict.get(self._get_payment_string(inv))

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.amount', 'state')
    def _compute_invoiced_itbis(self):
        for inv in self:
            if inv.type == 'in_invoice' and inv.state != 'draft':
                amount = 0
                for tax in inv.tax_line_ids:
                    if inv.currency_id != inv.company_id.currency_id and tax.tax_id.tax_group_id.name[:5] == 'ITBIS':
                        currency_id = inv.currency_id.with_context(date=inv.date_invoice)
                        amount += currency_id.compute(
                            abs(tax.amount), inv.company_id.currency_id)
                    elif tax.tax_id.tax_group_id.name[:5] == 'ITBIS':
                        amount += abs(tax.amount)
                inv.invoiced_itbis = amount

    # Partiendo de la documentacion de la DGII, los campos del 606 son los siguientes:

    # RNC o Cedula                          --> Viene de partner_id
    # Tipo Id                               --> Viene de partner_id
    # Tipo Bienes y Servicios Comprados     --> expense_type
    # NCF                                   --> move_name
    # NCF o Documento Modificado            --> origin
    # Fecha Comprobante                     --> Fecha factura
    # Fecha Pago                            --> Fecha en que la factura pasa a 'paid' ? *PENDIENTE VALIDAR*
    service_total_amount = fields.Monetary(compute='_compute_amount_fields', store=True)  # Monto Facturado en Servicios
    good_total_amount = fields.Monetary(compute='_compute_amount_fields', store=True)  # Monto Facturado en Bienes
    # Total Monto Facturado                 --> Campo amount_untaxed_signed
    invoiced_itbis = fields.Monetary(compute='_compute_invoiced_itbis', store=True)  # ITBIS Facturado
    withholded_itbis = fields.Monetary(compute='_compute_taxes_fields', store=True)  # Monto ITBIS Retenido
    # ITBIS sujeto a proporcionalidad       --> ? *PENDIENTE VALIDAR*
    # ITBIS llevado al Costo                --> ? *PENDIENTE VALIDAR*
    # ITBIS por Adelantar                   --> ITBIS Facturado - ITBIS llevado al Costo
    # ITBIS Percibido en compras            --> Este campo se va con 12 espacios en 0 para el 606
    isr_withholding_type = fields.Char(compute='_compute_isr_withholding_type', store=True, size=2)  # Tipo de Retención en ISR
    income_withholding = fields.Monetary(compute='_compute_taxes_fields', store=True)  # Monto Retención Renta
    # ISR Percibido en compras              --> Este campo se va con 12 espacios en 0 para el 606
    selective_tax = fields.Monetary(compute='_compute_taxes_fields', store=True)  # Monto Impuesto Selectivo al Consumo
    other_taxes = fields.Monetary(compute='_compute_taxes_fields', store=True)  # Monto Otros Impuestos/Tasas
    legal_tip = fields.Monetary(compute='_compute_taxes_fields', store=True)  # Monto Propina Legal
    payment_form = fields.Selection([('01', 'Cash'), ('02', 'Check / Transfer / Deposit'),  # Forma de pago
                                     ('03', 'Credit Card / Debit Card'), ('04', 'Credit'),
                                     ('05', 'Swap'), ('06', 'Credit Note'), ('07', 'Mixed')],
                                    compute='_compute_payment_form', store=True)

    # A partir de aqui, son campos unicos del 607
    payment_form_ids = fields.One2many('account.invoice.payment', 'invoice_id', string='Sale Payment Form')
