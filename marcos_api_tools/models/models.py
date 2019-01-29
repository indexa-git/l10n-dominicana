# -*- coding: utf-8 -*-

import requests

from odoo import models, api, exceptions, fields

import logging

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf
except(ImportError, IOError) as err:
    _logger.debug(err)


try:
    from stdnum.do import ncf
except(ImportError, IOError) as err:
    _logger.debug(err)


class MarcosApiTools(models.Model):
    _name = 'marcos.api.tools'

    @api.model
    def setup(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        http_proxy = config_parameter.get_param("http_proxy")
        if not http_proxy:
            config_parameter.create({"key": "http_proxy", "value": "False"})
        https_proxy = config_parameter.get_param("https_proxy")
        if not https_proxy:
            config_parameter.create({"key": "https_proxy", "value": "False"})
        api_marcos = config_parameter.get_param("api_marcos")
        if not api_marcos:
            config_parameter.create({"key": "api_marcos", "value": "http://api.marcos.do"})

    def get_marcos_api_request_params(self):

        config_parameter = self.env['ir.config_parameter'].sudo()
        http_proxy = config_parameter.get_param("http_proxy")
        https_proxy = config_parameter.get_param("https_proxy")
        api_marcos = config_parameter.get_param("api_marcos")

        if not api_marcos:
            raise exceptions.ValidationError(
                u"Debe configurar la URL de validación en línea: es la variable api_marcos en el menu de parametros del sistema")

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
            return requests.get("{}/central_bank_rates".format(request_params[1], proxies=request_params[2])).json()

    @api.multi
    def cron_auto_update_rates(self):
        try:
            usd = self.central_bank_rates()
            currency_id = self.env.ref("base.USD")
            if usd.get("dollar"):
                if usd["dollar"].get("selling_rate") and currency_id:
                    self.env["res.currency.rate"].create({"name": fields.Datetime.now(),
                                                          "rate": 1 / float(usd["dollar"]["selling_rate"]),
                                                          "currency_id": currency_id.id,
                                                          "company_id": self.env.user.id})
        except Exception as err:
            _logger.warning("call api.marcos.do raise {}".format(err))
