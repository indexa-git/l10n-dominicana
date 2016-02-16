# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions
import calendar
import base64
from tools import is_identification
import time


class DgiiExteriorReport(models.Model):
    _name = "dgii.exterior.report"

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'dgii.exterior.report'))
    name = fields.Char("Nombre")
    year = fields.Integer(u"Año", size=4, default=lambda s: int(time.strftime("%Y")))
    month = fields.Integer("Mes", size=2, default=lambda s: int(time.strftime("%m")))
    CANTIDAD_REGISTRO = fields.Integer("Cantidad de registros")
    TOTAL_MONTO_FACTURADO = fields.Float("TOTAL FACTURADO")
    report_lines = fields.One2many("dgii.exterior.report.line", "exterior_report_id")
    txt = fields.Binary("Reporte TXT", readonly=True)
    txt_name = fields.Char("Nombre del archivo",readonly=True)
    state = fields.Selection([('draft', 'Nuevo'), ('done', 'Generado')], default="draft")

    @api.model
    def create(self, vals):
        vals.update({"name": "{}/{}".format(vals["month"], vals["year"])})
        self = super(DgiiExteriorReport, self).create(vals)
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

            RAZON_SOCIAL = inv.partner_id.name

            TIPO_BIENES_SERVICIOS_COMPRADOS = inv.fiscal_position_id.supplier_fiscal_type

            if not TIPO_BIENES_SERVICIOS_COMPRADOS:
                raise exceptions.ValidationError(
                    u"Debe de definir el tipo de gasto para la posición fiscal {}!".format(inv.fiscal_position_id.name))

            FECHA_FACTURA = inv.date_invoice
            FECHA_RETENCION_ISR = False

            MONTO_FACTURADO = 0.00

            for line in inv.invoice_line_ids:
                account_ids = [l.account_id.id for l in line]
                move_lines = self.env["account.move.line"].search(
                    [('move_id', '=', inv.move_id.id), ('account_id', 'in', account_ids)])
                MONTO_FACTURADO += sum([l.debit for l in move_lines]) - sum([l.credit for l in move_lines])
                if inv.type == "in_refund":
                    MONTO_FACTURADO = MONTO_FACTURADO * -1

            MONTO_FACTURADO = MONTO_FACTURADO

            ISR_RETENCION = 0

            for tax in inv.tax_line_ids:
                if tax.tax_id.purchase_tax_type == "itbis":
                    raise exceptions.UserError("Impuesto invalido para el tipo de comprobante!")
                elif tax.tax_id.purchase_tax_type == "ritbis":
                    raise exceptions.UserError("Impuesto invalido para el tipo de comprobante!")
                else:
                    account_ids = [t.account_id.id for t in tax]
                    move_lines = self.env["account.move.line"].search(
                        [('move_id', '=', inv.move_id.id), ('account_id', 'in', account_ids)])
                    ISR_RETENCION += sum([l.debit for l in move_lines]) - sum([l.credit for l in move_lines]) * -1

            lines.append((0, False, {"LINE": LINE,
                                     "RAZON_SOCIAL": RAZON_SOCIAL,
                                     "TIPO_BIENES_SERVICIOS_COMPRADOS": TIPO_BIENES_SERVICIOS_COMPRADOS,
                                     "FECHA_FACTURA": FECHA_FACTURA,
                                     "FECHA_RETENCION_ISR": FECHA_RETENCION_ISR,
                                     "ISR_RETENCION": ISR_RETENCION,
                                     "MONTO_FACTURADO": MONTO_FACTURADO
                                     }))

            line_number += 1

        CANTIDAD_REGISTRO = len(lines)
        TOTAL_MONTO_FACTURADO = sum([line[2]["MONTO_FACTURADO"] for line in lines])


        res = self.write({"report_lines": lines,
                          "CANTIDAD_REGISTRO": CANTIDAD_REGISTRO,
                          "TOTAL_MONTO_FACTURADO": TOTAL_MONTO_FACTURADO,
                          "state": "done"})
        return res


    def generate_txt(self):
        if not self.company_id.vat or not is_identification(self.company_id.vat):
            raise exceptions.ValidationError("Debe de configurar el RNC de su empresa!")

        path = '/tmp/609{}.txt'.format(self.company_id.vat)
        file = open(path, 'w')
        lines = []

        header = "609"
        header += self.company_id.vat.zfill(11)
        header += str(self.year)
        header += str(self.month).zfill(2)
        header += "{:.2f}".format(self.TOTAL_MONTO_FACTURADO).zfill(16)
        lines.append(header)

        for line in self.report_lines:
            ln = ""
            ln += line.RAZON_SOCIAL.rjust(30)
            ln += line.TIPO_BIENES_SERVICIOS_COMPRADOS
            ln += line.FECHA_FACTURA.replace("-", "")
            ln += line.FECHA_RETENCION_ISR if line.FECHA_RETENCION_ISR else "".rjust(8)
            ln += "{:.2f}".format(line.ISR_RETENCION).zfill(12)
            ln += "{:.2f}".format(line.MONTO_FACTURADO).zfill(12)
            lines.append(ln)


        line_count = 1
        for l in lines:
            line_count += 1
            file.write(l + "\n")

        file.close()
        file = open(path, 'rb')
        report = base64.b64encode(file.read())
        report_name = 'DGII_609_{}_{}{}.TXT'.format(self.company_id.vat, str(self.year), str(self.month).zfill(2))
        self.write({'txt': report, 'txt_name': report_name})


    @api.multi
    def create_report(self):
        start_date, end_date = self.get_date_range()
        exterior_journal_ids = [rec.id for rec in self.env["account.journal"].search([('purchase_type', '=', 'exterior')])]
        invoices = self.env["account.invoice"].search([
            ('date_invoice', '>=', start_date),
            ('date_invoice', '<=', end_date),
            ('state', 'in', ('open', 'paid')),
            ('type', '=', 'in_invoice'),
            ('journal_id', 'in', exterior_journal_ids)
        ])
        self.create_report_lines(invoices)
        self.generate_txt()
        return True


class DgiiExteriorReportline(models.Model):
    _name = "dgii.exterior.report.line"

    exterior_report_id = fields.Many2one("dgii.exterior.report")
    LINE = fields.Integer("Linea")
    RNC_CEDULA = fields.Char(u"RNC", size=11)
    RAZON_SOCIAL = fields.Char("Razon Social")
    TIPO_IDENTIFICACION = fields.Char("Tipo ID", size=1)
    TIPO_BIENES_SERVICIOS_COMPRADOS = fields.Char("Tipo", size=2)
    FECHA_FACTURA = fields.Date("Fecha")
    FECHA_RETENCION_ISR = fields.Date("Fecha retencion ISR")
    ISR_RETENCION = fields.Float("ISR Retenido")
    MONTO_FACTURADO = fields.Float("Monto Facturado")
