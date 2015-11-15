# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import calendar
import base64
from tools import is_identification, is_ncf
import time

class DgiiCancelReport(models.Model):
    _name = "dgii.cancel.report"


    def get_default_period(self):
        self.year = int(time.strftime("%Y"))


    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('dgii.cancel.report'))
    name = fields.Char()
    year = fields.Integer(u"Año", size=4, default=lambda s: int(time.strftime("%Y")))
    month = fields.Integer("Mes", size=2, default=lambda s: int(time.strftime("%m")))
    CANTIDAD_REGISTRO = fields.Integer("Cantidad de registros")
    report_lines = fields.One2many("dgii.cancel.report.line", "cancel_report_id")
    txt = fields.Binary(u"Reporte TXT", readonly=True)
    txt_name = fields.Char(readonly=True)
    state = fields.Selection([('draft','Nuevo'),('done','Generado')], default="draft")


    @api.model
    def create(self, vals):
        vals.update({"name": "{}/{}".format(vals["month"],vals["year"])})
        self = super(DgiiCancelReport, self).create(vals)
        self.create_report()
        return self

    def get_date_range(self):
        if self.month > 12 or self.month < 1:
            self.month = False
            raise exceptions.ValidationError("El mes es invalido!")
        last_day = calendar.monthrange(self.year, self.month)[1]
        return ("{}-{}-{}".format(str(self.year), str(self.month).zfill(2), "01"),
                "{}-{}-{}".format(str(self.year), str(self.month).zfill(2), str(last_day).zfill(2)))

    def create_report_lines(self, invoices):
        if self._context.get("recreate", False):
            self.report_lines.unlink()
            self.txt = False
        lines = []
        line_number = 1
        for inv in invoices:
            line = []

            LINE = line_number

            NUMERO_COMPROBANTE_FISCAL = inv.move_name

            FECHA_COMPROBANTE = inv.date_invoice

            TIPO_ANULACION = inv.anulation_type

            lines.append((0,False,{"LINE":LINE,
                                   "NUMERO_COMPROBANTE_FISCAL":NUMERO_COMPROBANTE_FISCAL,
                                   "FECHA_COMPROBANTE":FECHA_COMPROBANTE,
                                   "TIPO_ANULACION": TIPO_ANULACION
                                   }))

            line_number += 1

        CANTIDAD_REGISTRO = len(lines)

        res = self.write({"report_lines": lines,
                           "CANTIDAD_REGISTRO": CANTIDAD_REGISTRO,
                           "state": "done"})

        return res

    def generate_txt(self):

        if not self.company_id.vat or not is_identification(self.company_id.vat):
            raise exceptions.ValidationError("Debe de configurar el RNC de su empresa!")

        path = '/tmp/608{}.txt'.format(self.company_id.vat)
        file = open(path,'w')
        lines = []

        header = "608"
        header += self.company_id.vat.zfill(11)
        header += str(self.year)
        header += str(self.month).zfill(2)
        lines.append(header)

        for line in self.report_lines:
            ln = ""
            ln += line.NUMERO_COMPROBANTE_FISCAL
            ln += line.FECHA_COMPROBANTE.replace("-","")
            ln += "{}".format(line.TIPO_ANULACION).zfill(12)
            lines.append(ln)

        for line in lines:
            file.write(line+"\n")

        file.close()
        file = open(path,'rb')
        report = base64.b64encode(file.read())
        report_name = 'DGII_608_{}_{}{}.TXT'.format(self.company_id.vat, str(self.year), str(self.month).zfill(2))
        self.write({'txt': report, 'txt_name': report_name})

    @api.multi
    def create_report(self):
        start_date, end_date = self.get_date_range()
        invoices = self.env["account.invoice"].search([('date_invoice','>=',start_date),
                                                       ('date_invoice','<=',end_date),
                                                       ('state','=','cancel'),
                                                       ('type','in',('out_invoice','out_refund'))])

        self.create_report_lines(invoices)
        self.generate_txt()
        return True


class DgiiCancelReportline(models.Model):
    _name = "dgii.cancel.report.line"


    cancel_report_id = fields.Many2one("dgii.cancel.report")
    LINE = fields.Integer("Linea")
    NUMERO_COMPROBANTE_FISCAL = fields.Char("NCF", size=19)
    FECHA_COMPROBANTE = fields.Date("Fecha")
    TIPO_ANULACION = fields.Char(u"Tipo de anulación", size=2)




