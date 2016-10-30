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
from odoo import models, fields, api, _, exceptions
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
import openerp.addons.decimal_precision as dp
from ..models.tools import is_ncf


class InheritedAccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    refund_ncf = fields.Char(u"NCF nota de crédito", size=19)
    invoice_type = fields.Char(default=lambda s: s._context.get("type", False))

    @api.onchange("refund_ncf")
    def onchange_ncf(self):
        if self.refund_ncf:
            if not is_ncf(self.refund_ncf, "in_refund"):
                self.refund_ncf = False
                return {
                    'warning': {'title': "Ncf invalido", 'message': "El numero de comprobante fiscal no es valido "
                                                                    "verifique de que no esta digitando un comprobante"
                                                                    "de consumidor final codigo 02 o revise si lo ha "
                                                                    "digitado incorrectamente"}
                }

    @api.multi
    def invoice_refund(self):

        res = super(InheritedAccountInvoiceRefund, self).invoice_refund()
        if self._context.get("type", False) == "in_invoice":
            action_domain = res.get("domain", False)
            if action_domain:
                refund_id = action_domain[1][2][0]
                self.env['account.invoice'].browse(refund_id).write({"move_name": self.refund_ncf, "ncf_required": True})

        return res
