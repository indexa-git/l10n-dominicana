# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
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
from openerp import models, api, _, fields
from openerp.exceptions import UserError, ValidationError
import openerp.addons.decimal_precision as dp


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        invoice = self._context.get('invoice', False)
        if invoice:
            if invoice.type in ('out_invoice', 'out_refund'):
                fiscal_position = invoice.fiscal_position_id.client_fiscal_type
                ncf_control = invoice.journal_id.ncf_control
                if fiscal_position != False and ncf_control == True:
                    if fiscal_position != 'final' and invoice.partner_id.vat == False:
                        raise ValidationError(u"Para este tipo de posición fiscal el relacionado debe de tener un RNC/Establecido!")
                invoice.set_ncf()
        return super(AccountMove, self).post()
    
    @api.model
    def create(self, vals):
        invoice = self._context.get("invoice", False)
        
        if invoice and invoice.type in ('in_invoice','in_refund'):
            pay_account = invoice.account_id.id
            if invoice.pay_to:
                for line in vals["line_ids"]:
                    if line[2]["account_id"] == pay_account:
                        line[2].update({"partner_id": invoice.pay_to.id})
            if invoice.charge_to:
                sale_journal = invoice.with_context({"type": "out_invoice"})._default_user_journal()
                out_invoice = invoice.copy({"type": "out_invoice",
                                            "partner_id": invoice.charge_to.id,
                                            "journal_id": sale_journal,
                                            "account_id": invoice.charge_to.property_account_receivable_id.id,
                                            "origin": "Factura de compra {}".format(invoice.number),
                                            "tax_line_ids": False,
                                            "fiscal_position_id": False,
                                            })
                for line in out_invoice.invoice_line_ids:
                    if line.product_id:
                        line.invoice_line_tax_ids = line.product_id.taxes_id
                        line._onchange_product_id()
                    else:
                        line.invoice_line_tax_ids = False

                out_invoice.compute_taxes()
                out_invoice._compute_amount()

        return super(AccountMove, self).create(vals)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.one
    @api.depends('debit','credit')
    def _bal(self):
        self.net = self.debit-self.credit

    net = fields.Float("Balance", compute=_bal, digits=dp.get_precision('Account'), store=True)

