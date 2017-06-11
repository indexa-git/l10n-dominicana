# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re


from odoo import api, fields, models

CURRENCY_DISPLAY_PATTERN = re.compile(r'(\w+)\s*(?:\((.*)\))?')


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    @api.multi
    def import_excel(self):
        return {}


class BcRateImport(models.TransientModel):
    _name = "bc.rate.import"

    excel_file = fields.Binary()

    @api.multi
    def import_excel(self):
        pass
