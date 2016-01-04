# -*- coding: utf-8 -*-


from openerp import models, fields, api, exceptions


class ShopJournalConfig(models.Model):
    _name = "shop.ncf.config"

    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.user.company_id.id, string=u"Compañia")
    name = fields.Char("Nombre", size=40, required=True)
    sale_journal_ids = fields.Many2many("account.journal", string="Diarios de ventas", required=False, domain="[('type','=','sale')]")
    user_ids = fields.Many2many("res.users", string="Usuarios que pueden usar esta sucursal")


    _sql_constraints = [
        ('shop_ncf_config_name_uniq', 'unique(name)', 'El nombre de la sucursal debe de ser unico!'),
    ]

    @api.model
    def get_user_shop_config(self):
        user_shops = self.search([('user_ids','=',self._uid)])
        if not user_shops:
            raise exceptions.UserError("Su usuario no tiene una sucursal asignada.")

        shop_ids = [rec.id for rec in user_shops]
        sale_journal_ids = list(set(sum([[sale_journal_id.id for sale_journal_id in rec.sale_journal_ids] for rec in user_shops], [])))

        if not sale_journal_ids:
            raise exceptions.UserError("Su sucursal no tiene diarios de facturas asignadas.")

        return {"shop_ids": shop_ids, "sale_journal_ids": sale_journal_ids}

    @api.model
    def setup_ncf(self):
        fiscal_posistions = self.env["account.fiscal.position"].search([])
        for position in fiscal_posistions:
            fiscal_code = position.name[0:2]
            if fiscal_code in ['01','02','03','04','05','06','07','08','09','10','11']:
                position.supplier = True
                position.supplier_fiscal_type = fiscal_code
            elif position.name == u"Para Crédito Fiscal":
                position.client_fiscal_type = "fiscal"
            elif position.name == "Consumidor Final":
                position.client_fiscal_type = "final"
            elif position.name == "Gubernamental":
                position.client_fiscal_type = "gov"
            elif position.name == u"Regímenes Especiales":
                position.client_fiscal_type = "special"

        final_prefix = u"A0100100102"
        fiscal_prefix = u"A0100100101"
        gov_prefix = u"A0100100114"
        esp_prefix = u"A0100100115"
        unique_prefix = u"A0100100112"
        nc_prefix = u"A0100100104"

        seq_values = {u'padding': 8,
                     u'code': False,
                     u'name': u'Facturas de cliente final',
                     u'implementation': u'standard',
                     u'company_id': 1,
                     u'use_date_range': False,
                     u'number_increment': 1,
                     u'prefix': u'A0100100102',
                     u'date_range_ids': [],
                     u'number_next_actual': 1,
                     u'active': True,
                     u'suffix': False}

        sale_journal = self.env["account.journal"].browse(1)

        if not sale_journal.final_sequence_id:
            seq_values["prefix"] = final_prefix
            seq_values["name"] = "Facturas de cliente final"
            final_id = self.env["ir.sequence"].create(seq_values)
            sale_journal.final_sequence_id = final_id.id

        if not sale_journal.fiscal_sequence_id:
            seq_values["prefix"] = fiscal_prefix
            seq_values["name"] = "Facturas de cliente fiscal"
            fiscal_id = self.env["ir.sequence"].create(seq_values)
            sale_journal.fiscal_sequence_id = fiscal_id.id

        if not sale_journal.gov_sequence_id:
            seq_values["prefix"] = gov_prefix
            seq_values["name"] = "Facturas de cliente gubernamental"
            gov_id = self.env["ir.sequence"].create(seq_values)
            sale_journal.gov_sequence_id = gov_id.id

        if not sale_journal.special_sequence_id:
            seq_values["prefix"] = esp_prefix
            seq_values["name"] = "Facturas de cliente especiales"
            esp_id = self.env["ir.sequence"].create(seq_values)
            sale_journal.special_sequence_id = esp_id.id


        if not sale_journal.unique_sequence_id:
            seq_values["prefix"] = unique_prefix
            seq_values["name"] = "Facturas unico ingreso"
            unique_id = self.env["ir.sequence"].create(seq_values)
            sale_journal.unique_sequence_id = unique_id.id


        if not sale_journal.refund_sequence_id:
            seq_values["prefix"] = nc_prefix
            seq_values["name"] = "Notas de credito"
            nc_id = self.env["ir.sequence"].create(seq_values)
            sale_journal.refund_sequence_id = nc_id.id

        shop = self.search([])
        if not shop:
            self.create({"name": "Principal", "sale_journal_id": [(4, 1, False)], "user_ids": [(4, 1, False)]})











