# -*- coding: utf-8 -*-


from openerp import models, fields, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    purchase_type = fields.Selection([("normal","Proveedor normal"),
                                      ("minor", "Gasto menor"),
                                      ("informal", "Proveedor informal"),
                                      ("exterior", "Pagos al exterior")
                                      ],
                                     string="Tipo de compra", default="normal")
    ncf_remote_validation = fields.Boolean("Validar NCF con DGII", default=True)
    final_sequence_id = fields.Many2one("ir.sequence", string="Secuencia para consumidor final")
    fiscal_sequence_id = fields.Many2one("ir.sequence", string="Secuencia para credito fiscal")
    gov_sequence_id = fields.Many2one("ir.sequence", string="Secuencia gubernamental")
    special_sequence_id = fields.Many2one("ir.sequence", string="Secuencia para regimenes especiales")
    unique_sequence_id = fields.Many2one("ir.sequence", string="Secuencia para unico ingreso")


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    supplier = fields.Boolean("Para proveedores")
    client_fiscal_type = fields.Selection([
        ("final", "Consumidor final"),
        ("fiscal", "Para credito fiscal"),
        ("gov", "Gubernamental"),
        ("special", "Regimenes especiales"),
        ("unico", "Unico ingreso")
    ], string="Tipo de comprobante")
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

    @api.model
    def get_fiscal_position(self, partner_id, delivery_id=None):
        if self.env.context.get("model", False) == "purchase.order":
            return super(AccountFiscalPosition, self).get_fiscal_position(partner_id, delivery_id=delivery_id)
        else:
            return self.get_fiscal_position_supplier(partner_id, delivery_id=delivery_id)

    @api.model
    def get_fiscal_position_supplier(self, partner_id, delivery_id=None):
        if not partner_id:
            return False
        # This can be easily overriden to apply more complex fiscal rules
        PartnerObj = self.env['res.partner']
        partner = PartnerObj.browse(partner_id)

        # if no delivery use invoicing
        if delivery_id:
            delivery = PartnerObj.browse(delivery_id)
        else:
            delivery = partner

        # partner manually set fiscal position always win
        if delivery.property_account_position_supplier_id or partner.property_account_position_supplier_id:
            return delivery.property_account_position_supplier_id.id or partner.property_account_position_supplier_id.id

        def fallback_search(vat_required):
            fpos = self._get_fpos_by_region(delivery.country_id.id, delivery.state_id.id, delivery.zip, vat_required)
            if not fpos:
                # Fallback on catchall (no country, no group)
                fpos = self.search([('auto_apply', '=', True), ('vat_required', '=', vat_required),
                                    ('country_id', '=', None), ('country_group_id', '=', None)], limit=1)
            return fpos

        # First search only matching VAT positions
        vat_required = bool(partner.vat)
        fp = fallback_search(vat_required)

        # Then if VAT required found no match, try positions that do not require it
        if not fp and vat_required:
            fp = fallback_search(False)

        return fp.id if fp else False


class AccountTax(models.Model):
    _inherit = 'account.tax'

    purchase_tax_type = fields.Selection([('itbis','ITBIS Pagado'),('ritbis','ITBIS Retenido'),('isr','ISR Retenido')],
                                         default="itbis", string="Tipo de impuesto de compra")