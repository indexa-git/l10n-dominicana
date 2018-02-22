# -*- coding: utf-8 -*-
from odoo import http
import json

import logging


_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except(ImportError, IOError) as err:
    _logger.debug(err)


class Odoojs(http.Controller):

    @http.route('/dgii_ws/<name>', auth='public')
    def index(self, name):
        result = rnc.search_dgii(name,end_at=20, start_at=1)
        return json.dumps(result)
