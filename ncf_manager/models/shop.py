# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

from odoo import models, fields, api


class ShopJournalConfig(models.Model):
    _name = "shop.ncf.config"
    _rec_name = 'branch_office'

    company_id = fields.Many2one("res.company", required=True,
                                 default=lambda s: s.env.user.company_id.id,
                                 string=u"Compañía")
    name = fields.Char("Prefijo NCF", size=9, copy=False)

    branch_office = fields.Char(string="Sucursal", required=True,
                                default=lambda obj: obj.env['ir.sequence'].next_by_code('branch.office'))

    journal_id = fields.Many2one("account.journal", string="Diario")
    ncf_control = fields.Boolean(string="", related='journal_id.ncf_control')

    final_active = fields.Boolean("Activo", default=True)
    final_sequence_id = fields.Many2one("ir.sequence", string="Secuencia")
    final_number_next_actual = fields.Integer(
        string=u"Próximo número", related="final_sequence_id.number_next_actual")
    final_max = fields.Integer(string=u"Número máximo")

    fiscal_active = fields.Boolean("Activo")
    fiscal_sequence_id = fields.Many2one("ir.sequence",
                                         string=u"Crédito fiscal")
    fiscal_number_next_actual = fields.Integer(string=u"Próximo número",
                                               related="fiscal_sequence_id.number_next_actual")
    fiscal_max = fields.Integer(string=u"Número máximo")

    gov_active = fields.Boolean("Activo")
    gov_sequence_id = fields.Many2one("ir.sequence", string="Gubernamental")
    gov_number_next_actual = fields.Integer(string=u"Próximo número",
                                            related="gov_sequence_id.number_next_actual")
    gov_max = fields.Integer(string=u"Número máximo")

    special_active = fields.Boolean("Activo")
    special_sequence_id = fields.Many2one("ir.sequence", string="Especiales")
    special_number_next_actual = fields.Integer(string=u"Próximo número",
                                                related="special_sequence_id.number_next_actual")
    special_max = fields.Integer(string=u"Número máximo")

    unico_active = fields.Boolean("Activo")
    unico_sequence_id = fields.Many2one("ir.sequence", string="Especiales")
    unico_number_next_actual = fields.Integer(string=u"Próximo número",
                                              related="unico_sequence_id.number_next_actual")
    unico_max = fields.Integer(string=u"Número máximo")

    nc_active = fields.Boolean("Activo")
    nc_sequence_id = fields.Many2one("ir.sequence", string=u"Nota de crédito")
    nc_number_next_actual = fields.Integer(string=u"Próximo número",
                                           related="nc_sequence_id.number_next_actual")
    nc_max = fields.Integer(string=u"Número máximo")

    nd_active = fields.Boolean("Activo")
    nd_sequence_id = fields.Many2one("ir.sequence", string=u"Nota de débito")
    nd_number_next_actual = fields.Integer(string=u"Próximo número",
                                           related="nd_sequence_id.number_next_actual")
    nd_max = fields.Integer(string=u"Número máximo")

    user_ids = fields.Many2many("res.users",
                                string="Usuarios que pueden usar estas secuencias")

    _sql_constraints = [
        ('shop_ncf_config_name_uniq',
         'unique(name, company_id)',
         u'¡El Prefijo NCF de la sucursal debe de ser único!'),
    ]

    @api.onchange("journal_id")
    def onchange_journal_id(self):
        if not self.ncf_control:

            self.name = lambda obj: obj.env['ir.sequence'].next_by_code(
                'name.shop')

    @api.onchange("name")
    def onchange_name(self):
        if self.name:
            if self.journal_id.ncf_control:
                if self.final_sequence_id:
                    self.final_sequence_id.write(
                        {"prefix": self.name + "02",
                         "name": "Facturas Cliente Final {}".format(self.name)})
                    self.fiscal_sequence_id.write(
                        {"prefix": self.name + "01",
                         "name": "Facturas Valor Fiscal {}".format(self.name)})
                    self.gov_sequence_id.write(
                        {"prefix": self.name + "15",
                         "name": "Facturas Gubernamentales {}".format(self.name)})
                    self.special_sequence_id.write(
                        {"prefix": self.name + "14",
                         "name": "Facturas Especiales {}".format(self.name)})
                    self.unico_sequence_id.write(
                        {"prefix": self.name + "12",
                         "name": u"Facturas de Único Ingreso {}".format(self.name)})
                    self.nc_sequence_id.write(
                        {"prefix": self.name + "04",
                         "name": u"Notas de Crédito {}".format(self.name)})
                    self.nd_sequence_id.write(
                        {"prefix": self.name + "03",
                         "name": u"Notas de Débito {}".format(self.name)})
                else:
                    self.setup_ncf(name=self.name,
                                   company_id=self.company_id.id,
                                   journal_id=self.journal_id.id, shop_id=self,
                                   branch_office=self.branch_office)

    @api.model
    def setup_ncf(self, name=False, company_id=False, journal_id=False,
                  user_id=False, shop_id=False, branch_office=False):

        name = name or "A01001001"
        branch_office = branch_office or "Sucursal"
        user = self.env.user
        company_id = company_id or user.company_id.id

        journal_obj = self.env['account.journal'].search(
            [('company_id', '=', company_id),
             ('type', '=', 'sale')],
            limit=1)

        journal_id = journal_id if journal_id else [journal for journal in journal_obj][0].id

        user_id = 1

        final_prefix = name + "02"
        fiscal_prefix = name + "01"
        gov_prefix = name + "15"
        esp_prefix = name + "14"
        nc_prefix = name + "04"
        nd_prefix = name + "03"
        unico_prefix = name + "12"

        if self.search_count(
                [('company_id', '=', company_id),
                 ('name', '=', name)]) == 0:
            if shop_id:
                shop = shop_id
            else:
                shop = self.create({"name": name,
                                    u"branch_office": branch_office,
                                    u"journal_id": journal_id,
                                    "user_ids": [(4, user_id, False)],
                                    "company_id": company_id,
                                    'final_max': 10000000,
                                    'fiscal_max': 10000000,
                                    'gov_max': 10000000,
                                    'special_max': 10000000,
                                    'nc_max': 10000000,
                                    'nd_max': 10000000,
                                    'unico_max': 10000000})

            seq_values = {'padding': 8,
                          'code': False,
                          'name': 'Facturas de cliente final',
                          'implementation': 'standard',
                          'company_id': 1,
                          'use_date_range': False,
                          'number_increment': 1,
                          'prefix': 'A0100100102',
                          'date_range_ids': [],
                          'number_next_actual': 1,
                          'active': True,
                          'suffix': False}

            seq_values["prefix"] = final_prefix
            seq_values["name"] = "Facturas de cliente final {}".format(name)
            final_id = self.env["ir.sequence"].create(seq_values)
            shop.final_sequence_id = final_id.id

            seq_values["prefix"] = fiscal_prefix
            seq_values["name"] = "Facturas de cliente fiscal {}".format(name)
            fiscal_id = self.env["ir.sequence"].create(seq_values)
            shop.fiscal_sequence_id = fiscal_id.id

            seq_values["prefix"] = gov_prefix
            seq_values["name"] = "Facturas de cliente gubernamental {}".format(
                name)
            gov_id = self.env["ir.sequence"].create(seq_values)
            shop.gov_sequence_id = gov_id.id

            seq_values["prefix"] = esp_prefix
            seq_values["name"] = "Facturas de cliente especiales {}".format(
                name)
            esp_id = self.env["ir.sequence"].create(seq_values)
            shop.special_sequence_id = esp_id.id

            seq_values["prefix"] = unico_prefix
            seq_values["name"] = "Facturas de unico ingreso {}".format(name)
            esp_id = self.env["ir.sequence"].create(seq_values)
            shop.unico_sequence_id = esp_id.id

            seq_values["prefix"] = nc_prefix
            seq_values["name"] = "Notas de credito {}".format(name)
            nc_id = self.env["ir.sequence"].create(seq_values)
            shop.nc_sequence_id = nc_id.id

            seq_values["prefix"] = nd_prefix
            seq_values["name"] = "Notas de debito {}".format(name)
            nd_id = self.env["ir.sequence"].create(seq_values)
            shop.refund_sequence_id = nc_id.id
            shop.nd_sequence_id = nd_id.id

            return shop

    def check_max(self, sale_fiscal_type, invoice):
        message = False

        if invoice.type == "out_refund" and self.nc_max >= self.nc_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Notas de Crédito para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "final" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Consumidor Final para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "fiscal" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Valor Fiscal para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "gov" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias Gubernamentales para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "special" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Regímenes Esp. para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

        elif sale_fiscal_type == "unico" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"Las secuencias de Único Ingreso para la sucursal {}"
            u" han sobrepasado el número máximo establecido, debe solicitar"
            u" más NCF para esta sucursal".format(self.name)

            invoice.message_post(body=message)

    @api.model
    def create(self, vals):
        if not vals['name']:
            vals['name'] = self.env['ir.sequence'].next_by_code('name.shop')
        return super(ShopJournalConfig, self).create(vals)
