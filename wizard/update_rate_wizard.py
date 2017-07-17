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

import requests


class UpdateRateWizard(models.TransientModel):
    _name = "update.rate.wizard"

    def _get_bank_rates(self):
        rates = []
        try:
            comerciales = self.env['marcos.api.tools'].rates()
            central = self.env['marcos.api.tools'].central_bank_rates()

            rates.append(("central-USD-{}".format(central['dollar']['selling_rate']),
                          "BANCO CENTRAL USD - {}".format(central['dollar']['selling_rate'])))

            for k, v in comerciales.iteritems():
                if k == 'bpd':
                    rates.append(("bpd-USD-{}".format(v['dollar']['selling_rate']),
                                  "BANCO POPULAR USD - {}".format(v['dollar']['selling_rate'])))
                    rates.append(("bpd-EUR-{}".format(v['euro']['selling_rate']),
                                  "BANCO POPULAR EUR - {}".format(v['euro']['selling_rate'])))
                if k == 'blh':
                    rates.append(("blh-USD-{}".format(v['dollar']['selling_rate']),
                                  "BANCO LOPEZ DE HARO USD - {}".format(v['dollar']['selling_rate'])))
                    rates.append(("blh-EUR-{}".format(v['euro']['selling_rate']),
                                  "BANCO LOPEZ DE HARO EUR - {}".format(v['euro']['selling_rate'])))
                if k == 'progress':
                    rates.append(("progress-USD-{}".format(v['dollar']['selling_rate']),
                                  "BANCO DOMINICANO DEL PROGRESO USD - {}".format(v['dollar']['selling_rate'])))
                    rates.append(("progress-EUR-{}".format(v['euro']['selling_rate']),
                                  "BANCO DOMINICANO DEL PROGRESO EUR - {}".format(v['euro']['selling_rate'])))
                if k == 'banreservas':
                    rates.append(("banreservas-USD-{}".format(v['dollar']['selling_rate']),
                                  "BANRESERVAS USD - {}".format(v['dollar']['selling_rate'])))
                    rates.append(("banreservas-EUR-{}".format(v['euro']['selling_rate']),
                                  "BANRESERVAS EUR - {}".format(v['euro']['selling_rate'])))
        except:
            pass

        return rates

    @api.model
    def default_get(self, fields):
        active_id = self._context.get("active_id", False)
        invoice_id = self.env["account.invoice"].browse(active_id)
        if not invoice_id.date_invoice:
            raise exceptions.ValidationError(u"Debe de especificar la fecha de la factura primero.")
        if invoice_id.state != "draft":
            raise exceptions.UserError(u"No puede cambiar la tasa porque la factura no está en estado borrador!")
        return super(UpdateRateWizard, self).default_get(fields)


    bank_rates = fields.Selection(_get_bank_rates, string="Tasa en bancos")
    custom_rate = fields.Boolean("Digitar tasa manualmente", default=True)
    currency_date = fields.Datetime("Tasa para la fecha")
    currency_id = fields.Many2one("res.currency", string="Moneda", domain=[('name', '!=', 'DOP')])
    rate = fields.Monetary("Tasa")

    @api.multi
    def change_rate(self):
        active_id = self._context.get("active_id", False)
        invoice_id = self.env["account.invoice"].browse(active_id)

        if not self.custom_rate:
            if invoice_id.date_invoice != fields.Date.today():
                raise exceptions.ValidationError(u"Solo puede usar las [Tasas de cambio para el día de hoy] si la factura es de hoy de lo contrario debe digitar tasa manualmente.")
            bank, cur, rate = self.bank_rates.split("-")

            self.env["res.currency.rate"].create({"name": fields.Datetime.now(),
                                                  "rate": 1 / float(rate),
                                                  "currency_id": invoice_id.currency_id.id,
                                                  "company_id": invoice_id.company_id.id})

        else:
            name = "{} {}".format(invoice_id.date_invoice, fields.Datetime.now().split(" ")[1])
            self.env["res.currency.rate"].create({"name": name,"rate": 1 / float(self.rate),"currency_id": invoice_id.currency_id.id,"company_id": invoice_id.company_id.id})
