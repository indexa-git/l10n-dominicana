# -*- coding: utf-8 -*-
import json
import re
import logging

from odoo import http

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc
except(ImportError, IOError) as err:
    _logger.debug(err)


class Odoojs(http.Controller):
    @http.route('/dgii_ws', auth='public', cors="*")
    def index(self, **kwargs):
        """
        Look for clients in the web service of the DGII
            :param self:
            :param **kwargs dict :the parameters received
            :param term string : the character of the client or his rnc /
        """
        term = kwargs.get("term", False)
        if term:
            if term.isdigit() and len(term) in [9, 11]:
                result = rnc.check_dgii(term)
            else:
                result = rnc.search_dgii(term, end_at=20, start_at=1)
            if not result is None:
                if not isinstance(result, list):
                    result = [result]

                for d in result:
                    d["name"] = " ".join(re.split("\s+", d["name"], flags=re.UNICODE))  # remove all duplicate white space from the name
                    d["label"] = u"{} - {}".format(d["rnc"], d["name"])
                return json.dumps(result)
