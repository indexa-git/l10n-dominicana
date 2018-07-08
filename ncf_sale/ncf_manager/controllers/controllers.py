# -*- coding: utf-8 -*-
import json
import re
import logging

from odoo import http

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except(ImportError, IOError) as err:
    _logger.debug(str(err))


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

    @http.route('/validate_rnc/', auth='public', cors="*")
    def validate_rnc(self, **kwargs):
        """
        Check if the number provided is a valid RNC
            :param self:
            :param **kwargs dict :the parameters received
            :param rnc string : the character of the client or his rnc
        """
        num = kwargs.get("rnc", False)
        if num.isdigit():
            if (len(num) == 9 and rnc.is_valid(num)) or (len(num) == 11 and cedula.is_valid(num)):
                try:
                    info = rnc.check_dgii(num)
                except Exception as err:
                    info = None
                    _logger.error(">>> " + str(err))

                if info is not None:
                    # remove all duplicate white space from the name
                    info["name"] = " ".join(re.split("\s+", info["name"], flags=re.UNICODE))

                return json.dumps({"is_valid": True, "info": info})

        return json.dumps({"is_valid": False})
