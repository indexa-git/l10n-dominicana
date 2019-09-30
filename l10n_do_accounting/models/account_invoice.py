# © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
# © 2018 Yasmany Castillo <yasmany003@gmail.com>
# © 2018 José López <jlopez@indexa.do>
# © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
# © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
# © 2018 Andrés Rodríguez <andres@iterativo.do>

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fiscal_type_id = fields.Many2one(
        'account.fiscal.type',
        string="Fiscal Type",
    )
    fiscal_sequence_id = fields.Many2one(
        'account.fiscal.sequence',
        string="Fiscal Sequence"
    )
    income_type = fields.Selection(
        [('01', '01 - Ingresos por Operaciones (No Financieros)'),
         ('02', '02 - Ingresos Financieros'),
         ('03', '03 - Ingresos Extraordinarios'),
         ('04', '04 - Ingresos por Arrendamientos'),
         ('05', '05 - Ingresos por Venta de Activo Depreciable'),
         ('06', '06 - Otros Ingresos')],
        string='Tipo de Ingreso',
        default=lambda self: self._context.get('income_type', '01'))

    expense_type = fields.Selection(
        [('01', '01 - Gastos de Personal'),
         ('02', '02 - Gastos por Trabajo, Suministros y Servicios'),
         ('03', '03 - Arrendamientos'), ('04', '04 - Gastos de Activos Fijos'),
         ('05', u'05 - Gastos de Representación'),
         ('06', '06 - Otras Deducciones Admitidas'),
         ('07', '07 - Gastos Financieros'),
         ('08', '08 - Gastos Extraordinarios'),
         ('09', '09 - Compras y Gastos que forman parte del Costo de Venta'),
         ('10', '10 - Adquisiciones de Activos'),
         ('11', '11 - Gastos de Seguros')],
        string="Tipo de Costos y Gastos")

    anulation_type = fields.Selection(
        [("01", "01 - Deterioro de Factura Pre-impresa"),
         ("02", u"02 - Errores de Impresión (Factura Pre-impresa)"),
         ("03", u"03 - Impresión Defectuosa"),
         ("04", u"04 - Corrección de la Información"),
         ("05", "05 - Cambio de Productos"),
         ("06", u"06 - Devolución de Productos"),
         ("07", u"07 - Omisión de Productos"),
         ("08", "08 - Errores en Secuencia de NCF"),
         ("09", "09 - Por Cese de Operaciones"),
         ("10", u"10 - Pérdida o Hurto de Talonarios")],
        string=u"Tipo de anulación",
        copy=False)

    origin_out = fields.Char("Afecta a")
    ncf_expiration_date = fields.Date(
        'Válido hasta',
        # compute="_compute_ncf_expiration_date",
        store=True,
    )
