# -*- coding: utf-8 -*-


from openerp import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    purchase_type = fields.Selection([("normal","Proveedor normal"),
                                      ("minor", "Gasto menor"),
                                      ("informal", "Proveedor informal"),
                                      ("exterior", "Pagos al exterior")
                                      ],
                                     string="Tipo de compra", default="normal")
    ncf_remote_validation = fields.Boolean("Validar NCF con DGII", default=True)


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    supplier = fields.Boolean("Para proveedores")
    client_fiscal_type = fields.Selection([
        ("final", "Consumidor final"),
        ("fiscal", "Para credito fiscal"),
        ("gov", "Gubernamental"),
        ("special", "Regimenes especiales")], string="Tipo de comprobante")
    journal_id = fields.Many2one("account.journal", string="Diario de compra", domain="[('type','=','purchase')]")
    supplier_fiscal_type = fields.Selection([
        ('01', '01 - Gastos de personal'),
        ('02', '02 - Gastos por trabajo, suministros y servicios'),
        ('03', '03 - Arrendamientos'),
        ('04', '04 - Gastos de Activos Fijos'),
        ('05', u'05 - Gastos de Representación'),
        ('06', '06 - Otras Deducciones Admitidas'),
        ('07', '07 - Gastos Financieros'),
        ('08', '08 - Gastos Extraordinarios'),
        ('09', '09 - Compras y Gastos que forman parte del Costo de Venta'),
        ('10', '10 - Adquisiciones de Activos'),
        ('11', '11 - Gastos de Seguro'),
    ], string="Tipo de gasto")


class AccountTax(models.Model):
    _inherit = 'account.tax'

    purchase_tax_type = fields.Selection([('itbis','ITBIS Pagado'),('ritbis','ITBIS Retenido'),('isr','ISR Retenido')],
                                         default="itbis", string="Tipo de impuesto de compra")