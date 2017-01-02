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
from odoo import models, api, _, fields
from odoo.exceptions import UserError


class AccountInvoiceCancel(models.TransientModel):
    """
    This wizard will cancel the all the selected invoices.
    If in the journal, the option allow cancelling entry is not selected then it will give warning message.
    """

    _inherit = "account.invoice.cancel"
    _description = "Cancel the Selected Invoices"

    anulation_type = fields.Selection([
        ("01", u"01 - DETERIORO DE FACTURA PRE-IMPRESA"),
        ("02", u"02 - ERRORES DE IMPRESIÓN (FACTURA PRE-IMPRESA)"),
        ("03", u"03 - IMPRESIÓN DEFECTUOSA"),
        ("04", u"04 - DUPLICIDAD DE FACTURA"),
        ("05", u"05 - CORRECCIÓN DE LA INFORMACIÓN"),
        ("06", u"06 - CAMBIO DE PRODUCTOS"),
        ("07", u"07 - DEVOLUCIÓN DE PRODUCTOS"),
        ("08", u"08 - OMISIÓN DE PRODUCTOS"),
        ("09", u"09 - ERRORES EN SECUENCIA DE NCF")
    ], string=u"Tipo de anulación", required=True)

    @api.multi
    def invoice_cancel(self):
        active_id = self._context.get("active_id", False)
        if active_id:
            invoice_id = self.env['account.invoice'].browse(active_id)
            invoice_id.anulation_type = self.anulation_type
            return invoice_id.action_invoice_cancel()
