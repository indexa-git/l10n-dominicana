# -*- coding: utf-8 -*-
# Part of Domincana Premium. See LICENSE file for full copyright and licensing details.

import json
from datetime import datetime as dt

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InvoiceServiceTypeDetail(models.Model):
    _name = 'invoice.service.type.detail'
    _description = "Invoice Service Type Detail"

    name = fields.Char()
    code = fields.Char(size=2)
    parent_code = fields.Char()

    _sql_constraints = [
        ('code_unique', 'unique(code)', _('Code must be unique')),
    ]


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _get_invoice_payment_widget(self, invoice_id):
        j = json.loads(invoice_id.payments_widget)
        return j['content'] if j else []

    def _compute_invoice_payment_date(self, invoices):
        for inv in invoices:
            if inv.state == 'paid':
                dates = [dt.strptime(payment['date'], '%Y-%m-%d') for payment in self._get_invoice_payment_widget(inv)]
                if dates:
                    inv.payment_date = max(dates).date()

    @api.multi
    @api.constrains('tax_line_ids')
    def _check_isr_tax(self):
        """Restrict one ISR tax per invoice"""
        for inv in self:
            line = [tax_line.tax_id.purchase_tax_type for tax_line in inv.tax_line_ids
                    if tax_line.tax_id.purchase_tax_type in ['isr', 'ritbis']]
            if len(line) != len(set(line)):
                raise ValidationError(_('An invoice cannot have multiple withholding taxes.'))

    def _convert_to_local_currency(self, inv, amount):
        sign = -1 if inv.type in ['in_refund', 'out_refund'] else 1
        if inv.currency_id != inv.company_id.currency_id:
            currency_id = inv.currency_id.with_context(date=inv.date_invoice)
            round_curr = currency_id.round
            amount = round_curr(currency_id.compute(amount, inv.company_id.currency_id))

        return amount * sign

    def _get_tax_line_ids(self, invoice):
        return invoice.tax_line_ids

    @api.multi
    @api.depends('tax_line_ids', 'tax_line_ids.amount', 'state')
    def _compute_taxes_fields(self):
        """Compute invoice common taxes fields"""
        for inv in self:

            fiscal_taxes = ['ISC', 'ITBIS', 'ISR', 'Propina']

            tax_line_ids = self._get_tax_line_ids(inv)

            if inv.state != 'draft':
                # Monto Impuesto Selectivo al Consumo
                inv.selective_tax = self._convert_to_local_currency(inv, sum(tax_line_ids.filtered(
                    lambda tax: tax.tax_id.tax_group_id.name == 'ISC').mapped('amount')))

                # Monto Otros Impuestos/Tasas
                inv.other_taxes = self._convert_to_local_currency(inv, sum(tax_line_ids.filtered(
                    lambda tax: tax.tax_id.tax_group_id.name == "Otros Impuestos").mapped('amount')))

                # Monto Propina Legal
                inv.legal_tip = self._convert_to_local_currency(inv, sum(tax_line_ids.filtered(
                    lambda tax: tax.tax_id.tax_group_id.name == 'Propina').mapped('amount')))

                # ITBIS sujeto a proporcionalidad
                inv.proportionality_tax = self._convert_to_local_currency(inv, sum(tax_line_ids.filtered(
                    lambda tax: tax.account_id.account_fiscal_type == 'A29').mapped('amount')))

                # ITBIS llevado al Costo
                inv.cost_itbis = self._convert_to_local_currency(inv, sum(tax_line_ids.filtered(
                    lambda tax: tax.account_id.account_fiscal_type == 'A51').mapped('amount')))

                if inv.type == 'in_invoice':
                    # Monto ITBIS Retenido
                    inv.withholded_itbis = self._convert_to_local_currency(inv, sum(tax_line_ids.filtered(
                        lambda tax: tax.tax_id.purchase_tax_type == 'ritbis').mapped('amount')))

                    # Monto Retención Renta
                    inv.income_withholding = self._convert_to_local_currency(inv, sum(tax_line_ids.filtered(
                        lambda tax: tax.tax_id.purchase_tax_type == 'isr').mapped('amount')))

                    if inv.state == 'paid' and inv.withholded_itbis or inv.income_withholding:
                        # Fecha Pago
                        self._compute_invoice_payment_date(inv)

    @api.multi
    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'state')
    def _compute_amount_fields(self):
        """Compute Purchase amount by product type"""
        for inv in self:
            if inv.type in ['in_invoice', 'in_refund'] and inv.state != 'draft':
                service_amount = 0
                good_amount = 0

                for line in inv.invoice_line_ids:
                    # Si la linea no tiene un producto
                    if not line.product_id:
                        service_amount += line.price_subtotal
                        continue

                    # Monto calculado en bienes
                    if line.product_id.type == 'product':
                        good_amount += line.price_subtotal

                    # Monto calculado en servicio
                    else:
                        service_amount += line.price_subtotal

                inv.service_total_amount = self._convert_to_local_currency(inv, service_amount)
                inv.good_total_amount = self._convert_to_local_currency(inv, good_amount)

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
                itbis_taxes = ['ITBIS', 'ITBIS 18%']
                for tax in self._get_tax_line_ids(inv):
                    if tax.tax_id.tax_group_id.name in itbis_taxes and tax.tax_id.purchase_tax_type != 'ritbis':
                        amount += tax.amount
                    inv.invoiced_itbis = self._convert_to_local_currency(inv, amount)

    @api.multi
    @api.depends('state')
    def _compute_third_withheld(self):
        for inv in self:
            if inv.state == 'paid':
                for payment in self._get_invoice_payment_widget(inv):
                    payment_id = self.env['account.payment'].browse(payment.get('account_payment_id'))
                    if payment_id:
                        # ITBIS Retenido por Terceros
                        inv.third_withheld_itbis = self._convert_to_local_currency(
                            inv, sum([move_line.debit for move_line in payment_id.move_line_ids
                                      if move_line.account_id.account_fiscal_type == 'A36']))

                        # Retención de Renta por Terceros
                        inv.third_income_withholding = self._convert_to_local_currency(
                            inv, sum([move_line.debit for move_line in payment_id.move_line_ids
                                      if move_line.account_id.account_fiscal_type == 'ISR']))

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
    service_total_amount = fields.Monetary(compute='_compute_amount_fields', store=True, currency_field='company_currency_id')
    good_total_amount = fields.Monetary(compute='_compute_amount_fields', store=True, currency_field='company_currency_id')
    invoiced_itbis = fields.Monetary(compute='_compute_invoiced_itbis', store=True, currency_field='company_currency_id')
    withholded_itbis = fields.Monetary(compute='_compute_taxes_fields', store=True, currency_field='company_currency_id')
    proportionality_tax = fields.Monetary(compute='_compute_taxes_fields', store=True, currency_field='company_currency_id')
    cost_itbis = fields.Monetary(compute='_compute_taxes_fields', store=True, currency_field='company_currency_id')
    advance_itbis = fields.Monetary(compute='_compute_advance_itbis', store=True, currency_field='company_currency_id')
    isr_withholding_type = fields.Char(compute='_compute_isr_withholding_type', store=True, size=2)
    income_withholding = fields.Monetary(compute='_compute_taxes_fields', store=True, currency_field='company_currency_id')
    selective_tax = fields.Monetary(compute='_compute_taxes_fields', store=True, currency_field='company_currency_id')
    other_taxes = fields.Monetary(compute='_compute_taxes_fields', store=True, currency_field='company_currency_id')
    legal_tip = fields.Monetary(compute='_compute_taxes_fields', store=True, currency_field='company_currency_id')
    payment_form = fields.Selection([('01', 'Cash'), ('02', 'Check / Transfer / Deposit'),
                                     ('03', 'Credit Card / Debit Card'), ('04', 'Credit'),
                                     ('05', 'Swap'), ('06', 'Credit Note'), ('07', 'Mixed')],
                                    compute='_compute_in_invoice_payment_form', store=True)
    third_withheld_itbis = fields.Monetary(compute='_compute_third_withheld', store=True, currency_field='company_currency_id')
    third_income_withholding = fields.Monetary(compute='_compute_third_withheld', store=True, currency_field='company_currency_id')
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
    fiscal_status = fields.Selection(
        [('normal', 'Partial'),
         ('done', 'Reported'),
         ('blocked', 'Not Sent')], copy=False,
        help="* The \'Grey\' status means ...\n"
             "* The \'Green\' status means ...\n"
             "* The \'Red\' status means ...\n"
             "* The blank status means that the invoice have not been included in a report.")


    @api.model
    def norma_recompute(self):
        """
        This method add all compute fields into []env add_todo and then recompute
        all compute fields in case dgii config change and need to recompute.
        :return:
        """
        active_ids = self._context.get("active_ids")
        invoice_ids = self.browse(active_ids)
        for k, v in self.fields_get().items():
            if v.get("store") and v.get("depends"):
                self.env.add_todo(self._fields[k], invoice_ids)

        self.recompute()
