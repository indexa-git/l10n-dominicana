# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################


from odoo import models, fields, api, exceptions


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def get_retention_amount(self):
        context = dict(self._context or {})
        active_model = context.get('active_model', False)
        active_ids = context.get('active_ids', False)
        retention_amount = 0

        invoices = self._get_invoices()

        if not invoices and active_ids:
            invoices = self.env[active_model].browse(active_ids)

        retention_invoices = invoices.filtered(lambda r: r.purchase_type == "informal")

        if retention_invoices:
            for inv in retention_invoices:
                retention_tax = inv.tax_line_ids.filtered(lambda r: r.tax_id.purchase_tax_type in ('ritbis', 'isr'))
                retention_amount = sum([abs(tax.amount) for tax in retention_tax])

        return retention_amount

    def _compute_total_invoices_amount(self):
        res = super(AccountPayment, self)._compute_total_invoices_amount()
        return res - self.get_retention_amount()

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if rec.get("amount", False):
            rec.update({"amount": rec["amount"]-self.get_retention_amount()})
        return rec


    @api.multi
    def post(self):
        super(AccountPayment, self).post()
        invoice_type = [inv.type for inv in self.invoice_ids]

        if "in_invoice" in invoice_type:
            self.create_retetion_move_line()


    @api.multi
    def create_retetion_move_line(self):
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        rml = []
        ctx = dict(self._context, from_payment=True)

        reconcile_invoice_move_line = aml_obj
        for rec in self:
            for inv in rec.invoice_ids:
                aiml = inv.with_context(ctx).tax_line_move_line_get()
                total, total_currency, biml = inv.compute_invoice_totals(inv.company_id.currency_id, aiml)
                for line in biml:
                    line.update({"name": u"{} / {}".format(line["name"], inv.number)})
                rml += biml
                reconcile_invoice_move_line |= inv.move_id.line_ids.filtered(lambda r: r.account_id.reconcile == True)


            part = self.env['res.partner']._find_accounting_partner(self.partner_id)
            lines = [(0, 0, inv.line_get_convert(l, part.id)) for l in rml]
            rcredit_amount = 0
            retention_line = []

            for line in lines:
                if line[2]["credit"] > 0:
                    rcredit_amount += line[2]["credit"]
                    retention_line.append(line)

            if retention_line:


                move = rec.move_line_ids[0].move_id

                reconcile_move_line = rec.move_line_ids.filtered(lambda r: r.debit > 0)

                reconcile_move_line.remove_move_reconcile()

                if not move.journal_id.update_posted:
                    move.journal_id.sudo().write({"update_posted": True})
                    move.button_cancel()
                    move.journal_id.sudo().write({"update_posted": False})
                else:
                    move.button_cancel()

                line_name = "Retenciones facturas "
                for line in reconcile_move_line:
                    line_name += line.invoice_id.number + " / "

                reconcile_invoice_move_line |= aml_obj.browse(reconcile_move_line[0].id).copy({"debit": rcredit_amount, "name": "{}".format(line_name)})
                reconcile_invoice_move_line |= reconcile_move_line

                for ml in retention_line:
                    ml[2].update({"move_id": move.id, "payment_id": rec.id})
                    aml_obj.create(ml[2])

                move.post()
                reconcile_invoice_move_line.reconcile()


class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"

    def get_retention_amount(self):
        context = dict(self._context or {})
        active_model = context.get('active_model', False)
        active_ids = context.get('active_ids', False)
        retention_amount = 0
        retention_invoices = False

        if active_ids:
            invoices = self.env[active_model].browse(active_ids)
            retention_invoices = invoices.filtered(lambda r: r.purchase_type == "informal")

        if retention_invoices:
            for inv in retention_invoices:
                retention_tax = inv.tax_line_ids.filtered(lambda r: r.tax_id.purchase_tax_type in ('ritbis', 'isr'))
                retention_amount = sum([abs(tax.amount) for tax in retention_tax])

        return retention_amount

    @api.model
    def default_get(self, fields):
        rec = super(account_register_payments, self).default_get(fields)
        rec.update({"amount": rec["amount"] - self.get_retention_amount()})
        return rec





