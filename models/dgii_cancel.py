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
from odoo import models, fields, api, exceptions
import calendar
import base64
import time
import re
import io


class DgiiCancelReport(models.Model):
    _name = "dgii.cancel.report"

    def get_default_period(self):
        self.year = int(time.strftime("%Y"))

    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'dgii.cancel.report'))
    name = fields.Char(u"Descripción")
    year = fields.Integer(u"Año", size=4,
                          default=lambda s: int(time.strftime("%Y")))
    month = fields.Integer("Mes", size=2,
                           default=lambda s: int(time.strftime("%m")))
    CANTIDAD_REGISTRO = fields.Integer(u"Cantidad de registros")
    report_lines = fields.One2many("dgii.cancel.report.line",
                                   "cancel_report_id")
    txt = fields.Binary("Reporte TXT", readonly=True)
    txt_name = fields.Char("Nombre del Archivo", readonly=True)
    state = fields.Selection([('draft', 'Nuevo'),
                              ('done', 'Generado')], default="draft")

    @api.model
    def create(self, vals):
        vals.update({"name": "{}/{}".format(vals["month"], vals["year"])})
        self = super(DgiiCancelReport, self).create(vals)
        self.create_report()
        return self

    def get_date_range(self):
        if self.month > 12 or self.month < 1:
            self.month = False
            raise exceptions.ValidationError(u"¡El mes es inválido!")
        last_day = calendar.monthrange(self.year, self.month)[1]
        return (
            "{}-{}-{}".format(str(self.year), str(self.month).zfill(2), "01"),
            "{}-{}-{}".format(str(self.year), str(self.month).zfill(2),
                              str(last_day).zfill(2))
            )

    def create_report_lines(self, invoices):
        if self._context.get("recreate", False):
            self.report_lines.unlink()
            self.txt = False
        lines = []
        line_number = 1
        for inv in invoices:
            LINE = line_number
            NUMERO_COMPROBANTE_FISCAL = inv.move_name
            FECHA_COMPROBANTE = inv.date_invoice
            TIPO_ANULACION = inv.anulation_type
            lines.append((0, False,
                         {"LINE": LINE,
                          "NUMERO_COMPROBANTE_FISCAL":
                          NUMERO_COMPROBANTE_FISCAL,
                          "FECHA_COMPROBANTE": FECHA_COMPROBANTE,
                          "TIPO_ANULACION": TIPO_ANULACION}))

            line_number += 1

        CANTIDAD_REGISTRO = len(lines)

        res = self.write({"report_lines": lines,
                          "CANTIDAD_REGISTRO": CANTIDAD_REGISTRO,
                          "state": "done"})

        return res

    def generate_txt(self):
        if not self.company_id.vat:
            raise exceptions.ValidationError(
                u"Para poder generar el 608 primero debe especificar el RNC/"
                u"Cédula de la compañia.")

        company_fiscal_identificacion = re.sub("[^0-9]", "", self.company_id.vat)

        if not company_fiscal_identificacion or not self.env['res.partner'].is_identification(company_fiscal_identificacion):
            raise exceptions.ValidationError(u"¡Debe configurar el RNC de"
                                             " su empresa!")

        path = '/tmp/608{}.txt'.format(company_fiscal_identificacion)
        file = io.open(path, 'w', encoding="utf-8", newline='\r\n')
        lines = []

        header = "608"
        header += company_fiscal_identificacion.zfill(11)
        header += str(self.year)
        header += str(self.month).zfill(2)
        lines.append(header)

        for line in self.report_lines:
            ln = ""
            ln += line.NUMERO_COMPROBANTE_FISCAL
            ln += line.FECHA_COMPROBANTE.replace("-", "")
            ln += "{}".format(line.TIPO_ANULACION).zfill(2)
            lines.append(ln)

        for line in lines:
            file.write(line + "\n")

        file.close()
        file = open(path, 'rb')
        report = base64.b64encode(file.read())
        report_name = 'DGII_608_{}_{}{}.TXT'.format(
                                                company_fiscal_identificacion,
                                                str(self.year),
                                                str(self.month).zfill(2))
        self.write({'txt': report, 'txt_name': report_name})

    @api.multi
    def create_report(self):
        start_date, end_date = self.get_date_range()
        invoices = self.env["account.invoice"].search(
            [('date_invoice', '>=', start_date),
             ('date_invoice', '<=', end_date),
             ('state', '=', 'cancel'),
             ('type', 'in', ('out_invoice', 'out_refund'))]
            )

        self.create_report_lines(invoices)
        self.generate_txt()
        return True


class DgiiCancelReportline(models.Model):
    _name = "dgii.cancel.report.line"

    cancel_report_id = fields.Many2one("dgii.cancel.report")
    LINE = fields.Integer(u"Línea")
    NUMERO_COMPROBANTE_FISCAL = fields.Char("NCF", size=19)
    FECHA_COMPROBANTE = fields.Date("Fecha")
    TIPO_ANULACION = fields.Char(u"Tipo de anulación", size=2)
