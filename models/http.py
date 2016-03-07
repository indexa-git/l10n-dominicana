# -*- coding: utf-8 -*-

from openerp import http

db_filter_org = http.db_filter


def db_filter(dbs, httprequest=None):
    dbs = db_filter_org(dbs, httprequest)
    httprequest = httprequest or http.request.httprequest
    db_filter_hdr = httprequest.environ.get('HTTP_X_ODOO_DBFILTER')
    if not dbs and db_filter_hdr:
        dbs = [db_filter_hdr]
    return dbs

http.db_filter = db_filter