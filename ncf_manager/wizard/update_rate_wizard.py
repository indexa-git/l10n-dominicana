# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

from odoo import models, fields, api, exceptions


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
