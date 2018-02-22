# -*- coding: utf-8 -*-
from odoo import http
import json
import requests

import logging

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except(ImportError, IOError) as err:
    _logger.debug(err)


class Odoojs(http.Controller):

    @http.route('/dgii_ws', auth='public')
    def index(self, **kwargs):
        if kwargs.get("term", False):
            result = rnc.search_dgii(kwargs["term"], end_at=20, start_at=1)
            if not result is None:
                result = ["{}||{}".format(d["rnc"], d["name"]) for d in result]
                return json.dumps(result)
