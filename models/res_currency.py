# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import openpyxl
from odoo import api, fields, models
from tempfile import TemporaryFile

import logging

_logger = logging.getLogger(__name__)

CURRENCY_DISPLAY_PATTERN = re.compile(r'(\w+)\s*(?:\((.*)\))?')


class Currency(models.Model):
    _inherit = "res.currency"

    bc_rate_xls = fields.Binary(string=u"Histórico en Excel de Tasas del Banco"
                                       " Central")

    @api.multi
    def update_rate_from_files(self):
        month_dict = {"Ene": "01",
                      "Feb": "02",
                      "Mar": "03",
                      "Abr": "04",
                      "May": "05",
                      "Jun": "06",
                      "Jul": "07",
                      "Ago": "08",
                      "Sep": "09",
                      "Oct": "10",
                      "Nov": "11",
                      "Dic": "12"
                      }

        self.env["res.currency.rate"].search([('currency_id', '=', 3)]).unlink()

        file = self.bc_rate_xls.decode('base64')
        excel_fileobj = TemporaryFile('wb+')
        excel_fileobj.write(file)
        excel_fileobj.seek(0)
        # Create workbook
        workbook = openpyxl.load_workbook(excel_fileobj, data_only=True)
        # Get the first sheet of excel file
        sheet = workbook[workbook.get_sheet_names()[0]]

        for row in sheet.rows:
            if row[0].value is None:
                break
            year = str(row[0].value)
            month = month_dict[row[1].value.strip()]
            day = str(row[2].value).zfill(2)
            name = "{}-{}-{} {}".format(year, month, day, fields.Datetime.now().split(" ")[1])
            rate = float(row[4].value)
            self.env["res.currency.rate"].create({"name": name,
                                                  "rate": 1 / rate,
                                                  "currency_id": 3})
            _logger.info("UDS rate create {}".format(name))

    @api.multi
    def _compute_current_rate(self):
        """
        Orveride native because whan to show rate_id on invoice to be shure
         and do not search rate by datetime just by date because RD have rate by day
        :return:
        """
        date = self._context.get('date') or fields.Datetime.now()
        company_id = self._context.get('company_id') or self.env['res.users']._get_company().id
        # the subquery selects the last rate before 'date' for the given currency/company
        query = """SELECT c.id, (SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name::date = %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1) AS rate
                   FROM res_currency c
                   WHERE c.id IN %s"""

        self._cr.execute(query, (date, company_id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())

        query = """SELECT r.currency_id, r.id FROM res_currency_rate r
                                  WHERE r.currency_id IN %s AND r.name::date = %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1"""

        self._cr.execute(query, (tuple(self.ids), date, company_id))
        rate_ids = dict(self._cr.fetchall())

        for currency in self:
            currency.rate = currency_rates.get(currency.id) or 1.0
            currency.res_currency_rate_id = rate_ids.get(currency.id) or False

    res_currency_rate_id = fields.Integer(compute=_compute_current_rate)


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    @api.multi
    @api.depends("rate")
    def _get_converted(self):
        for rec in self:
            if rec.rate > 0:
                rec.converted = 1 / rec.rate

    @api.multi
    def name_get(self):
        result = []
        for rate in self:
            result.append((rate.id, "{} | Tasa: {}".format(rate.name, rate.converted)))
        return result

    rate = fields.Float(digits=(12, 12), help='The rate of the currency to the currency of rate 1')
    converted = fields.Float(compute=_get_converted, digits=(12, 4))
