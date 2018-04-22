# -*- coding: utf-8 -*-

import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# SERVICE_TYPE_DETAIL = [('11', 'Sueldo y Salario'),
#                        ('12', 'Otros Gastos de Personal'),
#                        ('21', 'Honorarios por Servicios Profesionales (Personas Morales)'),
#                        ('22', 'Honorarios por Servicios Profesionales (Personas Físicas)'),
#                        ('23', 'Seguridad, Mensajería, Transporte y otros Servicios (Personas Físicas)'),
#                        ('24', 'Seguridad, Mensajería, Transporte y otros Servicios (Personas Morales)'),
#                        ('31', 'De Inmuebles (A Personas Físicas)'),
#                        ('32', 'De Inmuebles (A Personas Morales)'),
#                        ('33', 'Otros Arrendamientos'),
#                        ('41', 'Reparación'),
#                        ('42', 'Mantenimiento'),
#                        ('51', 'Relaciones Públicas'),
#                        ('52', 'Publicidad Promocional'),
#                        ('53', 'Promocional'),
#                        ('54', 'Otros Gastos de Representación'),
#                        ('61', 'Por Préstamos con Bancos'),
#                        ('62', 'Por Préstamos con Financiamiento'),
#                        ('63', 'Por Préstamos con Personas Físicas'),
#                        ('64', 'Por Préstamos con Organismos Internacionales'),
#                        ('65', 'Otros Gastos Financieros'),
#                        ('71', 'Gastos de Seguro'),
#                        ('81', 'Cesión / Uso Marca'),
#                        ('82', 'Transferencias de Know-How'),
#                        ('83', 'Cesión / Uso de Patente'),
#                        ('84', 'Otras Regalías')]


class InvoiceServiceTypeDetail(models.Model):
    _name = 'invoice.service.type.detail'

    name = fields.Char()
    code = fields.Char(size=2)
    parent_code = fields.Char()

    _sql_constraints = [
        ('code_unique', 'unique(code)', _('Code must be unique')),
    ]


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
        """Compute invoice common taxes fields"""
        for inv in self:
            if inv.state != 'draft':
                # Monto Impuesto Selectivo al Consumo
                inv.selective_tax = abs(sum([tax.amount for tax in inv.tax_line_ids
                                             if tax.tax_id.tax_group_id.name == 'ISC']))

                # Monto Otros Impuestos/Tasas
                inv.other_taxes = abs(sum([tax.amount for tax in inv.tax_line_ids
                                           if tax.tax_id.purchase_tax_type not in ['isr', 'ritbis']
                                           and tax.tax_id.tax_group_id.name[:5] not in ['ISC', 'ITBIS']]))

                # Monto Propina Legal
                inv.legal_tip = abs(sum([tax.amount for tax in inv.tax_line_ids
                                         if tax.tax_id.tax_group_id.name == 'Propina']))

                # ITBIS sujeto a proporcionalidad
                inv.proportionality_tax = abs(sum([tax.amount for tax in inv.tax_line_ids
                                                   if tax.account_id.account_fiscal_type == 'A29']))

                # ITBIS llevado al Costo
                inv.cost_itbis = abs(sum([tax.amount for tax in inv.tax_line_ids
                                          if tax.account_id.account_fiscal_type == 'A51']))

                if inv.type == 'in_invoice' and inv.state == 'paid':
                    # Monto ITBIS Retenido
                    inv.withholded_itbis = abs(sum([tax.amount for tax in inv.tax_line_ids
                                                    if tax.tax_id.purchase_tax_type == 'ritbis']))

                    # Monto Retención Renta
                    inv.income_withholding = abs(sum([tax.amount for tax in inv.tax_line_ids
                                                      if tax.tax_id.purchase_tax_type == 'isr']))
                if inv.state == 'paid':
                    # Fecha Pago
                    inv.payment_date = fields.Date.context_today(inv)

    @api.multi
    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'state')
    def _compute_amount_fields(self):
        """Compute Purchase amount by product type"""
        for inv in self:
            if inv.type == 'in_invoice' and inv.state != 'draft':
                # Monto calculado en servicio
                inv.service_total_amount = sum([line.price_subtotal for line in inv.invoice_line_ids
                                                if line.product_id.type == 'service'])

                # Monto calculado en bienes
                inv.good_total_amount = sum([line.price_subtotal for line in inv.invoice_line_ids
                                             if line.product_id.type != 'service'])

    @api.multi
    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'state')
    def _compute_isr_withholding_type(self):
        """Compute ISR Withholding Type

        Keyword / Values:
        01 -- Alquileres
        02 -- Honorarios por Servicios
        03 -- Otras Rentas
        04 -- Rentas Presuntas
        05 -- Intereses Pagados a Personas Jurídicas
        06 -- Intereses Pagados a Personas Físicas
        07 -- Retención por Proveedores del Estado
        08 -- Juegos Telefónicos
        """
        for inv in self:
            if inv.type == 'in_invoice' and inv.state != 'draft':
                isr = [tax_line.tax_id for tax_line in inv.tax_line_ids if tax_line.tax_id.purchase_tax_type == 'isr']
                if isr:
                    inv.isr_withholding_type = isr.pop(0).isr_retention_type

    def _get_invoice_payment_widget(self, invoice_id):
        j = json.loads(invoice_id.payments_widget)
        return j['content'] if j else []

    def _get_payment_string(self, invoice_id):
        """Compute Vendor Bills payment method string

        Keyword / Values:
        cash        -- Efectivo
        bank        -- Cheques / Transferencias / Depósitos
        card        -- Tarjeta Crédito / Débito
        credit      -- Compra a Crédito
        swap        -- Permuta
        credit_note -- Notas de Crédito
        mixed       -- Mixto
        """
        payments = []
        p_string = ""

        for payment in self._get_invoice_payment_widget(invoice_id):
            payment_id = self.env['account.payment'].browse(payment.get('account_payment_id'))
            if payment_id:
                if payment_id.journal_id.type in ['cash', 'bank']:
                    p_string = payment_id.journal_id.payment_form

            # If invoice is paid, but the payment doesn't come from
            # a journal, assume it is a credit note
            payment = p_string if payment_id else 'credit_note'
            payments.append(payment)

        methods = {p for p in payments}
        if len(methods) == 1:
            return list(methods)[0]
        elif len(methods) > 1:
            return 'mixed'

    @api.multi
    @api.depends('state')
    def _compute_in_invoice_payment_form(self):
        for inv in self:
            if inv.state == 'paid':
                payment_dict = {'cash': '01', 'bank': '02', 'card': '03', 'credit': '04', 'swap': '05',
                                'credit_note': '06', 'mixed': '07'}
                inv.payment_form = payment_dict.get(self._get_payment_string(inv))
            else:
                inv.payment_form = '04'

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.amount', 'state')
    def _compute_invoiced_itbis(self):
        """Compute invoice invoiced_itbis taking into account the currency"""
        for inv in self:
            if inv.state != 'draft':
                amount = 0
                for tax in inv.tax_line_ids:
                    if inv.currency_id != inv.company_id.currency_id and tax.tax_id.tax_group_id.name[:5] == 'ITBIS':
                        currency_id = inv.currency_id.with_context(date=inv.date_invoice)
                        amount += currency_id.compute(
                            abs(tax.amount), inv.company_id.currency_id)
                    elif tax.tax_id.tax_group_id.name[:5] == 'ITBIS':
                        amount += abs(tax.amount)
                inv.invoiced_itbis = amount

    @api.multi
    @api.depends('state')
    def _compute_third_withheld(self):
        for inv in self:
            if inv.state == 'paid':
                for payment in self._get_invoice_payment_widget(inv):
                    payment_id = self.env['account.payment'].browse(payment.get('account_payment_id'))
                    if payment_id:
                        # ITBIS Retenido por Terceros
                        inv.third_withheld_itbis = sum([move_line.debit for move_line in payment_id.move_line_ids
                                                        if move_line.account_id.account_fiscal_type == 'A36'])

                        # Retención de Renta por Terceros
                        inv.third_income_withholding = sum([move_line.debit for move_line in payment_id.move_line_ids
                                                            if move_line.account_id.account_fiscal_type == 'ISR'])

    @api.multi
    @api.depends('invoiced_itbis', 'cost_itbis', 'state')
    def _compute_advance_itbis(self):
        for inv in self:
            if inv.state != 'draft':
                inv.advance_itbis = inv.invoiced_itbis - inv.cost_itbis

    @api.multi
    @api.depends('journal_id.purchase_type')
    def _compute_is_exterior(self):
        for inv in self:
            inv.is_exterior = True if inv.journal_id.purchase_type == 'exterior' else False

    @api.onchange('service_type')
    def onchange_service_type(self):
        self.service_type_detail = False
        return {'domain': {'service_type_detail': [('parent_code', '=', self.service_type)]}}

    @api.onchange('journal_id')
    def ext_onchange_journal_id(self):
        self.service_type = False
        self.service_type_detail = False

    # ISR Percibido                         --> Este campo se va con 12 espacios en 0 para el 606
    # ITBIS Percibido                       --> Este campo se va con 12 espacios en 0 para el 606
    payment_date = fields.Date(compute='_compute_taxes_fields', store=True)
    service_total_amount = fields.Monetary(compute='_compute_amount_fields', store=True)
    good_total_amount = fields.Monetary(compute='_compute_amount_fields', store=True)
    invoiced_itbis = fields.Monetary(compute='_compute_invoiced_itbis', store=True)
    withholded_itbis = fields.Monetary(compute='_compute_taxes_fields', store=True)
    proportionality_tax = fields.Monetary(compute='_compute_taxes_fields', store=True)
    cost_itbis = fields.Monetary(compute='_compute_taxes_fields', store=True)
    advance_itbis = fields.Monetary(compute='_compute_advance_itbis', store=True)
    isr_withholding_type = fields.Char(compute='_compute_isr_withholding_type', store=True, size=2)
    income_withholding = fields.Monetary(compute='_compute_taxes_fields', store=True)
    selective_tax = fields.Monetary(compute='_compute_taxes_fields', store=True)
    other_taxes = fields.Monetary(compute='_compute_taxes_fields', store=True)
    legal_tip = fields.Monetary(compute='_compute_taxes_fields', store=True)
    payment_form = fields.Selection([('01', 'Cash'), ('02', 'Check / Transfer / Deposit'),
                                     ('03', 'Credit Card / Debit Card'), ('04', 'Credit'),
                                     ('05', 'Swap'), ('06', 'Credit Note'), ('07', 'Mixed')],
                                    compute='_compute_in_invoice_payment_form', store=True)
    third_withheld_itbis = fields.Monetary(compute='_compute_third_withheld', store=True)
    third_income_withholding = fields.Monetary(compute='_compute_third_withheld', store=True)
    is_exterior = fields.Boolean(compute='_compute_is_exterior', store=True)
    service_type = fields.Selection([('01', 'Gastos de Personal'),
                                     ('02', 'Gastos por Trabajos, Suministros y Servicios'),
                                     ('03', 'Arrendamientos'),
                                     ('04', 'Gastos de Activos Fijos'),
                                     ('05', 'Gastos de Representación'),
                                     ('06', 'Gastos Financieros'),
                                     ('07', 'Gastos de Seguros'),
                                     ('08', 'Gastos por Regalías y otros Intangibles')])
    service_type_detail = fields.Many2one('invoice.service.type.detail')
