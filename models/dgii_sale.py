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


class DgiiSaleReport(models.Model):
    _name = "dgii.sale.report"

    @api.one
    @api.depends("ITBIS_TOTAL", "TOTAL_MONTO_FACTURADO")
    def _calc_total(self):

        self.TOTAL_MONTO_FACTURAS = sum([line.MONTO_FACTURADO for line in self.report_lines if not line.NUMERO_COMPROBANTE_MODIFICADO.strip()])
        self.TOTAL_MONTO_NC = sum([line.MONTO_FACTURADO for line in self.report_lines if line.NUMERO_COMPROBANTE_MODIFICADO.strip()])
        self.ITBIS_TOTAL_FACTURAS = sum([line.ITBIS_FACTURADO for line in self.report_lines if not line.NUMERO_COMPROBANTE_MODIFICADO.strip()])
        self.ITBIS_TOTAL_NC = sum([line.ITBIS_FACTURADO for line in self.report_lines if line.NUMERO_COMPROBANTE_MODIFICADO.strip()])
        self.TOTAL_VENTA = self.TOTAL_MONTO_FACTURAS-self.TOTAL_MONTO_NC
        self.TOTAL_VENTA_ITBIS = self.ITBIS_TOTAL_FACTURAS-self.ITBIS_TOTAL_NC

    def get_default_period(self):
        self.year = int(time.strftime("%Y"))

    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('dgii.sale.report'))
    name = fields.Char("Nombre")
    year = fields.Integer(u"Año", size=4,
                          default=lambda s: int(time.strftime("%Y")))
    month = fields.Integer(u"Mes", size=2,
                           default=lambda s: int(time.strftime("%m")))
    CANTIDAD_REGISTRO = fields.Integer(u"Cantidad de registros")
    ITBIS_TOTAL = fields.Float(u"ITBIS FACTURADO")
    TOTAL_MONTO_FACTURADO = fields.Float(
                                    u"TOTAL FACTURADO",
                                    help="Suma de las facturas y las notas de"
                                    " crédito como se digitan en el formulario"
                                    " de la DGII")

    TOTAL_MONTO_FACTURAS = fields.Float(u"FACTURADO", compute=_calc_total)
    TOTAL_MONTO_NC = fields.Float(u"NOTAS CRÉDITO", compute=_calc_total)
    ITBIS_TOTAL_FACTURAS = fields.Float(u"ITBIS FACTURADO", compute=_calc_total)
    ITBIS_TOTAL_NC = fields.Float(u"ITBIS NOTAS CRÉDITO", compute=_calc_total)
    TOTAL_VENTA = fields.Float(u"VENTA", compute=_calc_total)
    TOTAL_VENTA_ITBIS = fields.Float(u"ITBIS", compute=_calc_total)

    report_lines = fields.One2many("dgii.sale.report.line", "sale_report_id")
    txt = fields.Binary(u"Reporte TXT", readonly=True)
    txt_name = fields.Char("Nombre del archivo", readonly=True)
    state = fields.Selection([('draft', 'Nuevo'),
                             ('done', 'Generado')], default="draft")

    @api.model
    def create(self, vals):
        vals.update({"name": "{}/{}".format(vals["month"], vals["year"])})
        self = super(DgiiSaleReport, self).create(vals)
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
            if inv.sale_fiscal_type == "final":
                RNC_CEDULA = ""
                TIPO_IDENTIFICACION = "3"
            else:
                if not inv.partner_id.vat:
                    raise exceptions.UserError(u"El cliente para la factura {} no tiene RNC/Cédula.".format(inv.number))
                RNC_CEDULA = re.sub("[^0-9]", "", inv.partner_id.vat.strip())
                TIPO_IDENTIFICACION = "1" if len(str(RNC_CEDULA).strip()) == 9 else "2"

            if not self.env['marcos.api.tools'].is_ncf(inv.number, inv.type):
                raise exceptions.ValidationError(
                    u"¡El número de NCF o el RNC/Cédula del clienten para el"
                    u" comprobante {} no es válido!".format(inv.number))

            NUMERO_COMPROBANTE_MODIFICADO = "".rjust(19)
            if inv.type == "out_invoice":
                NUMERO_COMPROBANTE_FISCAL = inv.number
            elif inv.type == "out_refund":
                NUMERO_COMPROBANTE_FISCAL = inv.number
                NUMERO_COMPROBANTE_MODIFICADO = inv.origin

            FECHA_COMPROBANTE = inv.date_invoice
            if inv.payment_move_line_ids:
                FECHA_PAGO = max(inv.payment_move_line_ids).date
            else:
                FECHA_PAGO = False

            account_ids = list(set([l.account_id.id for l in inv.invoice_line_ids if l.account_id.user_type_id.name == 'Ingreso']))

            move_lines = self.env["account.move.line"].search(
                            [('move_id', '=', inv.move_id.id),
                             ('account_id', 'in', account_ids)])
            MONTO_FACTURADO = abs(sum([l.credit for l in move_lines]) -
                                  sum([l.debit for l in move_lines]))

            if not MONTO_FACTURADO:
                MONTO_FACTURADO = 0

            ITBIS_FACTURADO = 0

            for tax in inv.tax_line_ids:
                account_ids  = [t.account_id.id for t in tax]
                move_lines = self.env["account.move.line"].search(
                                [('move_id', '=', inv.move_id.id),
                                 ('account_id', 'in', account_ids)])
                ITBIS_FACTURADO += (sum([l.debit for l in move_lines]) -
                                    sum([l.credit for l in move_lines])*-1)
                if inv.type == "out_refund":
                    ITBIS_FACTURADO = ITBIS_FACTURADO

            lines.append(
                (0, False,
                 {"LINE": LINE,
                  "RNC_CEDULA": RNC_CEDULA,
                  "TIPO_IDENTIFICACION": TIPO_IDENTIFICACION,
                  "NUMERO_COMPROBANTE_FISCAL": NUMERO_COMPROBANTE_FISCAL,
                  "NUMERO_COMPROBANTE_MODIFICADO": NUMERO_COMPROBANTE_MODIFICADO,
                  "FECHA_COMPROBANTE": FECHA_COMPROBANTE,
                  "FECHA_PAGO": FECHA_PAGO,
                  "ITBIS_FACTURADO": ITBIS_FACTURADO,
                  "MONTO_FACTURADO": MONTO_FACTURADO}))

            line_number += 1

        CANTIDAD_REGISTRO = len(lines)
        ITBIS_TOTAL = sum([line[2]["ITBIS_FACTURADO"] for line in lines])
        TOTAL_MONTO_FACTURADO = sum([line[2]["MONTO_FACTURADO"] for line in lines])

        res = self.write({"report_lines": lines,
                          "CANTIDAD_REGISTRO": CANTIDAD_REGISTRO,
                          "ITBIS_TOTAL": ITBIS_TOTAL,
                          "TOTAL_MONTO_FACTURADO": TOTAL_MONTO_FACTURADO,
                          "state": "done"})
        return res

    def generate_txt(self):
        if not self.company_id.vat:
            raise exceptions.ValidationError(
                u"Para poder generar el 607 primero debe especificar el RNC/"
                u"Cédula de la compañia.")

        company_fiscal_identificacion = re.sub("[^0-9]", "",
                                               self.company_id.vat)

        if not company_fiscal_identificacion or not self.env['marcos.api.tools'].is_identification(company_fiscal_identificacion):
            raise exceptions.ValidationError("Debe de configurar el RNC de su empresa!")

        path = '/tmp/607{}.txt'.format(company_fiscal_identificacion)
        file = open(path, 'w')
        lines = []

        header = "607"
        header += company_fiscal_identificacion.rjust(11)
        header += str(self.year)
        header += str(self.month).zfill(2)
        header += "{:.2f}".format(self.CANTIDAD_REGISTRO).zfill(12)
        header += "{:.2f}".format(self.TOTAL_MONTO_FACTURADO).zfill(16)
        lines.append(header)

        for line in self.report_lines:
            ln = ""
            ln += line.RNC_CEDULA.rjust(11)
            ln += line.TIPO_IDENTIFICACION
            ln += line.NUMERO_COMPROBANTE_FISCAL
            ln += line.NUMERO_COMPROBANTE_MODIFICADO
            ln += line.FECHA_COMPROBANTE.replace("-", "")
            # ln += line.FECHA_PAGO.replace("-","") if line.FECHA_PAGO else
            # "".rjust(8)
            ln += "{:.2f}".format(line.ITBIS_FACTURADO).zfill(12)
            ln += "{:.2f}".format(line.MONTO_FACTURADO).zfill(12)
            lines.append(ln)

        for line in lines:
            file.write(line + "\n")

        file.close()
        file = open(path, 'rb')
        report = base64.b64encode(file.read())
        report_name = 'DGII_607_{}_{}{}.TXT'.format(
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
             ('state', 'in', ('open', 'paid')),
             ('type', 'in', ('out_invoice', 'out_refund'))])
        self.create_report_lines(invoices)
        self.generate_txt()
        return True


class DgiiSaleReportline(models.Model):
    _name = "dgii.sale.report.line"

    sale_report_id = fields.Many2one("dgii.sale.report")
    LINE = fields.Integer("Linea")
    RNC_CEDULA = fields.Char(u"RNC", size=11)
    TIPO_IDENTIFICACION= fields.Char("Tipo ID", size=1)
    NUMERO_COMPROBANTE_FISCAL = fields.Char("NCF", size=19)
    NUMERO_COMPROBANTE_MODIFICADO = fields.Char("Afecta", size=19)
    FECHA_COMPROBANTE = fields.Date("Fecha")
    FECHA_PAGO = fields.Date("Pagado")
    ITBIS_FACTURADO = fields.Float("ITBIS Facturado")
    MONTO_FACTURADO = fields.Float("Monto Facturado")
