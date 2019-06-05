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
from openerp import models, api


class PrintCheck(models.AbstractModel):
    _name = 'report.l10n_do_check_printing.check_print_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'account.payment'  # self.env.context.get('active_model')
        payment_ids = self.env[model].browse(docids)
        """
        payments = []
        for payment in payments: # _ids:
            payment.payment_date
            year, month, day = payment.payment_date.split("-")
            payment.report_date = "{} {} {} {} {} {} {} {}".format(
                day[0], day[1], month[0], month[1], year[0], year[1], year[2],
                year[3])
            payment.report_amount = '{:20,.2f}'.format(payment.amount).strip()
            payment.report_communication = payment.communication.rstrip(
                '\r|\n') if payment.communication else ""

            payments.append(payment)
        """
        return {
            "doc_ids": docids,
            "doc_model": model,
            "docs": payment_ids,
        }

