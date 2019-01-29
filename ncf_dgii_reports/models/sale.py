from odoo import models, fields, api
from calendar import monthrange as mr
from stdnum.do import rnc
from datetime import datetime as dt
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import base64
from odoo.exceptions import ValidationError
import io

payment_methods = {"cash": ("01", "01 - Efectivo"),
                   "bank": ("02", u"02 - Cheque / Transferencia / Depósito"),
                   "card": ("03", u"03 - Tarjeta Crédito / Débito"),
                   "credit": ("04", u"04 - A Crédito"),
                   "swap": ("05", "05 - Permuta"),
                   "nota_credito": ("06", "06 - Notas de Credito"),
                   "mixto": ("07", "07 - Mixto")}


class DgiiSaleReport(models.Model):
    _name = "dgii.sale.report"

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    name = fields.Char()
    year = fields.Integer(u"Año", size=4, default=lambda s: int(fields.date.today().year))
    month = fields.Integer("Mes", size=2, default=lambda s: int(fields.date.today().month))
    reg_count = fields.Integer("Cantidad de registros")
    retain_tax_amount = fields.Float("Total ITBIS Retenido")
    tax_amount = fields.Float("Total ITBIS Pagado")
    invoice_amount = fields.Float("Total Facturado")
    RETENCION_RENTA = fields.Float(u"Total Retención ISR")
    report_lines = fields.One2many("dgii.sale.report.line", "purchase_report_id")
    txt = fields.Binary("Reporte TXT", readonly=True)
    txt_name = fields.Char("Nombre del archivo", readonly=True)
    state = fields.Selection([('draft', 'Nuevo'), ('done', 'Generado')], default="draft")
    service_amount = fields.Float(string="Total Facturado Servicios")
    goods_amount = fields.Float(string="Total Facturado Bienes")

    def get_invoices(self):
        invoice_ids = self.env['account.invoice'].search(
            [('type', '=', 'in_invoice'), ('state', 'in', ['open', 'paid']),
             ('date_invoice', '>=', '01-%s-%s' % (self.month, self.year)),
             ('date_invoice', '<=', "%s-%s-%s" % (mr(self.year, self.month)[1], self.month, self.year))])
        paid_out_invoices = self.env['account.payment'].search(
            [('payment_type', '=', 'outbound'),
             ('payment_date', '>=', '01-%s-%s' % (self.month, self.year)),
             ('payment_date', '<=', "%s-%s-%s" % (mr(self.year, self.month)[1], self.month, self.year))]).mapped(
            'invoice_ids')

        sequence = 1
        self.report_lines.unlink()
        for invoice_id in list(set(invoice_ids.ids) | set(paid_out_invoices.ids)):
            self.env['dgii.sale.report.line'].create({"invoice_id": invoice_id,
                                                          "sequence": sequence,
                                                          "purchase_report_id": self.id})
            sequence += 1
        self.reg_count = sequence - 1
        self._get_amounts()
        self._generate_txt()

    @api.model
    def create(self, vals):
        vals.update({"name": "{}/{}".format(vals["month"], vals["year"])})
        return super(DgiiSaleReport, self).create(vals)

    @api.one
    @api.depends("report_lines")
    def _get_amounts(self):
        self.retain_tax_amount = sum(self.report_lines.mapped('retain_tax_amount'))
        self.tax_amount = sum(self.report_lines.mapped('tax_amount'))
        self.service_amount = sum(self.report_lines.mapped('service_amount'))
        self.goods_amount = sum(self.report_lines.mapped('goods_amount'))

        self.invoice_amount = self.retain_tax_amount + self.tax_amount + self.service_amount + self.goods_amount

    def _generate_txt(self):
        valid_message = u"Para poder generar el 606 primero debe especificar el RNC/Cédula de la compañia."

        if not self.company_id.vat:
            raise ValidationError(valid_message)

        is_rnc = len(self.company_id.vat) == 9 or len(self.company_id.vat) == 11
        if not is_rnc and not rnc.validate(self.company_id.vat):
            raise ValidationError(valid_message)

        path = '/tmp/606{}.txt'.format(self.company_id.vat)
        file = io.open(path, 'w', encoding="utf-8", newline='\r\n')
        lines = []
        file.write("606|%s|%s%s|%s" % (self.company_id.vat, self.year, self.month, self.reg_count) + "\n")

        for line in self.report_lines:
            ln = ""
            ln += line.vat + "|"
            ln += line.vat_type + "|"
            ln += line.expense_type + "|"
            ln += line.reference + "|"
            ln += line.origin_out or "" + "|"
            ln += line.ncf_date.replace("-", "").replace("/", "") + "|"
            if line.ncf_payment_date:
                ln += line.ncf_payment_date.replace("-", "").replace("/", "") + "|"
            else:
                ln += "|"
            ln += "%s|" % (round(line.service_amount, 2) if line.service_amount else "")
            ln += "%s|" % (round(line.goods_amount, 2) if line.goods_amount else "")
            ln += "%s|" % (round(line.invoice_amount, 2) if line.invoice_amount else "")
            ln += "%s|" % (round(line.tax_amount, 2) if line.tax_amount else "")
            ln += "%s|" % (round(line.retain_tax_amount, 2) if line.retain_tax_amount else "")
            ln += "%s|" % (round(line.tax_proporcional, 2) if line.tax_proporcional else "")
            ln += "%s|" % (round(line.tax_cost, 2) if line.tax_cost else "")
            ln += "%s|" % (round(line.tax_advance, 2) if line.tax_advance else "")
            ln += "%s|" % (round(line.tax_buy, 2) if line.tax_buy else "")
            ln += "%s|" % (line.isr_retention_type or "")
            ln += "%s|" % (round(line.isr_retention_amount, 2) if line.isr_retention_amount else "")
            ln += "%s|" % (round(line.isr_buy, 2) if line.isr_buy else "")
            ln += "%s|" % (round(line.isc_amount, 2) if line.isc_amount else "")
            ln += "|"
            ln += "%s|" % (round(line.propina_legal, 2) if line.propina_legal else "")
            ln += "%s" % (line.payment_method or "")
            lines.append(ln)

        for line in lines:
            file.write(line + "\n")

        file.close()
        file = open(path, 'rb')
        report = base64.b64encode(file.read())
        report_name = 'DGII_F_606_{}_{}{}.TXT'.format(self.company_id.vat, str(self.year), str(self.month))
        self.write({'txt': report, 'txt_name': report_name})


class DgiiSaleReportLine(models.Model):
    _name = "dgii.sale.report.line"

    sequence = fields.Integer(string='Linea')

    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    number = fields.Char(related="invoice_id.number", string="Factura")
    expense_type = fields.Selection(related="invoice_id.expense_type")
    expense_code = fields.Char(string="Expense Code")
    purchase_report_id = fields.Many2one('dgii.sale.report')
    vat = fields.Char(related="invoice_id.partner_id.vat", string="RNC o Cedula")
    reference = fields.Char(related="invoice_id.reference", string="NCF")
    origin_out = fields.Char(related="invoice_id.origin_out", string="NCF Modificado")
    vat_type = fields.Char(string="Tipo ID", size=2)
    ncf_date = fields.Date(related="invoice_id.date_invoice", string="Fecha de NCF")
    ncf_payment_date = fields.Date(string="Fecha de Pago")
    service_amount = fields.Float(string="Monto Facturado Servicios", default=0.0)
    goods_amount = fields.Float(string="Monto Facturado Bienes", default=0.0)
    invoice_amount = fields.Float(string="Monto Facturado", default=0.0)
    tax_amount = fields.Float(string="ITBIS Facturado", default=0.0)
    retain_tax_amount = fields.Float(string="ITBIS Retenido", default=0.0)
    tax_proporcional = fields.Float(string="ITBIS sujeto a Proporcionalidad (Art. 349)", default=0.0)
    tax_cost = fields.Float(string="ITBIS llevado al Costo", default=0.0)
    tax_advance = fields.Float(string="ITBIS por Adelantar", default=0.0)
    tax_buy = fields.Float(string="ITBIS percibido en compras", default=0.0)
    isr_retention_type = fields.Selection(
        [('01', 'Alquileres'),
         ('02', 'Honorarios por Servicios'),
         ('03', 'Otras Rentas'),
         ('04', 'Rentas Presuntas'),
         ('05', u'Intereses Pagados a Personas Jurídicas'),
         ('06', u'Intereses Pagados a Personas Físicas'),
         ('07', u'Retención por Proveedores del Estado'),
         ('08', u'Juegos Telefónicos')],
        string="Tipo de Retención en ISR"
    )
    isr_retention_amount = fields.Float(string="Retencion Renta")
    isr_buy = fields.Float(string="ISR Compras")
    isc_amount = fields.Float(string="ISC")
    propina_legal = fields.Float(string="Propina Legal")
    payment_method = fields.Selection([("01", "01 - Efectivo"),
                                       ("02", u"02 - Cheque / Transferencia / Depósito"),
                                       ("03", u"03 - Tarjeta Crédito / Débito"),
                                       ("04", u"04 - A Crédito"),
                                       ("05", "05 - Permuta"),
                                       ("06", "06 - Notas de Credito"),
                                       ("07", "07 - Mixto")], string="Forma de Pago")

    @api.one
    def _get_expense_code(self):
        self.expense_code = self.expense_type

    @api.one
    def _get_vat_type(self):
        is_rnc = len(self.vat) == 9
        if is_rnc and rnc.validate(self.vat):
            self.vat_type = "1"
        else:
            self.vat_type = "2"

    @api.one
    def _compute_ncf_date(self):
        ncf_date = dt.strptime(self.invoice_id.date_invoice, DEFAULT_SERVER_DATE_FORMAT)
        if self.invoice_id.payment_ids:
            ncf_payment_date = dt.strptime(max(self.invoice_id.payment_ids).payment_date,
                                           DEFAULT_SERVER_DATE_FORMAT)

            start_date = '%s-%s-01' % (self.purchase_report_id.year, self.purchase_report_id.month)
            end_date = "%s-%s-%s" % (
                self.purchase_report_id.year, self.purchase_report_id.month,
                mr(self.purchase_report_id.year, self.purchase_report_id.month)[1])

            if ncf_payment_date >= dt.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT) and \
                    ncf_payment_date <= dt.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT):
                self.ncf_payment_date = ncf_payment_date

    @api.one
    def _compute_payment_method(self):
        if self.invoice_id.payment_ids and self.ncf_payment_date:
            payment_method = max(self.invoice_id.payment_ids).journal_id.payment_form
            if payment_method:
                self.payment_method = str(payment_methods.get(payment_method)[0])
        else:
            self.payment_method = "04"

    @api.one
    def _get_amounts(self):
        invoice_line_ids = self.invoice_id.invoice_line_ids
        tax_line_ids = self.invoice_id.tax_line_ids
        cuenta_bienes = self.env.ref("l10n_do.do_niif_51010100")
        cuenta_servicios = self.env.ref("l10n_do.do_niif_51010200")
        isc_tax = self.env.ref("l10n_do.tax_10_telco")
        propina_legal = self.env.ref("l10n_do.tax_tip_purch")

        self.goods_amount = sum(
            invoice_line_ids.filtered(lambda il: il.account_id.id == cuenta_bienes.id).mapped('price_subtotal'))

        self.service_amount = sum(invoice_line_ids.filtered(
            lambda il: il.account_id.id == cuenta_servicios.id).mapped('price_subtotal'))

        self.tax_amount = sum(tax_line_ids.filtered(lambda tax_line: tax_line.amount_total > 0).mapped('amount_total'))

        if self.ncf_payment_date:
            self.retain_tax_amount = abs(
                sum(tax_line_ids.filtered(lambda tl: tl.amount_total < 0).mapped('amount_total')))

        self.tax_advance = self.tax_amount - self.tax_cost

        self.invoice_amount = self.invoice_id.amount_untaxed

        self.isc_amount = sum(tax_line_ids.filtered(lambda tl: tl.tax_id.id == isc_tax.id).mapped('amount_total'))

        self.propina_legal = sum(
            tax_line_ids.filtered(lambda tl: tl.tax_id.id == propina_legal.id).mapped('amount_total'))

    @api.one
    def _get_isr_type(self):
        isr_retention_type = self.invoice_id.tax_line_ids.filtered(
            lambda tax_line: tax_line.tax_id.purchase_tax_type == "isr")
        if isr_retention_type:
            self.isr_retention_amount = sum(isr_retention_type.mapped("amount_total"))
            self.isr_retention_type = max(isr_retention_type).tax_id.isr_retention_type

    @api.model
    def create(self, vals):
        report_line = super(DgiiSaleReportLine, self).create(vals)
        report_line._get_expense_code()
        report_line._get_vat_type()
        report_line._compute_ncf_date()
        report_line._get_amounts()
        report_line._get_isr_type()
        report_line._compute_payment_method()
        return report_line
