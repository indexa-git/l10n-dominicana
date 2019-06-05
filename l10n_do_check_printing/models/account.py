# -*- coding: utf-8 -*-
###############################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL.
#  (<https://marcos.do/>) 
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it,
# unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without
# copying any source code or material from the Software. You may distribute
# those modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Softwar or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

from odoo import api, models, fields


class InheritedAccountJournal(models.Model):
    _inherit = "account.journal"

    check_layout = fields.Many2one(
        "check.report.config",
        string="Plantilla de cheque",
        required=False,
        help=u"Seleccione el formato que corresponde al papel en el que va a"
        u" imprimir sus cheques en.\n Para desactivar la función de impresión,"
        " seleccione 'Ninguno'.")


class InheritedPrintPreNumberedChecks(models.TransientModel):
    _inherit = 'print.prenumbered.checks'

    @api.multi
    def print_checks(self):
        check_number = self.next_check_number
        payments = self.env['account.payment'].browse(self.env.context['payment_ids'])
        payments.filtered(lambda r: r.state == 'draft').post()
        payments.filtered(lambda r: r.state not in ('sent', 'cancelled')).write({'state': 'sent'})
        for payment in payments:
            payment.check_number = check_number
            check_number += 1
        return payments.do_print_checks()
