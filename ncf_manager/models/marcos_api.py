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

import requests

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class MarcosApiTools(models.Model):
    _name = 'marcos.api.tools'

    @api.model
    def _setup(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        http_proxy = config_parameter.get_param("http_proxy")
        if not http_proxy:
            config_parameter.create({"key": "http_proxy", "value": "False"})
        https_proxy = config_parameter.get_param("https_proxy")
        if not https_proxy:
            config_parameter.create({"key": "https_proxy", "value": "False"})
        api_marcos = config_parameter.get_param("api_marcos")
        if not api_marcos:
            config_parameter.create(
                {"key": "api_marcos", "value": "http://api.marcos.do"})

    def get_marcos_api_request_params(self):
        import ipdb; ipdb.set_trace()
        config_parameter = self.env['ir.config_parameter'].sudo()
        test_param = config_parameter.get_param("http_proxy")

        if test_param == 'False':
            self._setup()

        http_proxy = config_parameter.get_param("http_proxy")
        https_proxy = config_parameter.get_param("https_proxy")
        api_marcos = config_parameter.get_param("api_marcos")

        if not api_marcos:
            raise ValidationError(
                _(u"Debe configurar la URL de validación en línea. \nEs la variable api_marcos en el menu de parametros del sistema"))

        proxies = {}
        if http_proxy != "False":
            proxies.update({"http": http_proxy})

        if http_proxy != "False":
            proxies.update({"https": https_proxy})

        return (1, api_marcos, proxies)

    def rates(self):
        request_params = self.get_marcos_api_request_params()
        if request_params[0] == 1:
            return requests.get("{}/rates".format(request_params[1], proxies=request_params[2])).json()

    def central_bank_rates(self):
        request_params = self.get_marcos_api_request_params()
        if request_params[0] == 1:
            return requests.get("{}/central_bank_rates".format(
                request_params[1],
                proxies=request_params[2])).json()

    @api.multi
    def cron_auto_update_rates(self):
        try:
            usd = self.central_bank_rates()
            currency_id = self.env.ref("base.USD")
            if usd.get("dollar"):
                if usd["dollar"].get("selling_rate") and currency_id:
                    self.env["res.currency.rate"].create(
                        {"name": fields.Datetime.now(),
                         "rate": 1 / float(usd["dollar"]["selling_rate"]),
                         "currency_id": currency_id.id,
                         "company_id": self.env.user.id})
        except Exception as err:
            _logger.warning("call api.marcos.do raise {}".format(err))
