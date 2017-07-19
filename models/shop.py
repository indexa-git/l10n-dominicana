# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################

from odoo import models, fields, api, exceptions


class ShopJournalConfig(models.Model):
    _name = "shop.ncf.config"

    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.user.company_id.id,
                                 string=u"Compañia")
    name = fields.Char("Prefijo NCF", size=9, required=True, copy=False)

    journal_id = fields.Many2one("account.journal", string="Diario", required=True)

    final_active = fields.Boolean("Activo")
    final_sequence_id = fields.Many2one("ir.sequence", string=u"Secuencia")
    final_number_next_actual = fields.Integer(string=u"Próximo número", related="final_sequence_id.number_next_actual")
    final_max = fields.Integer(string=u"Número máximo")

    fiscal_active = fields.Boolean("Activo")
    fiscal_sequence_id = fields.Many2one("ir.sequence", string=u"Credito fiscal")
    fiscal_number_next_actual = fields.Integer(string=u"Próximo número",
                                               related="fiscal_sequence_id.number_next_actual")
    fiscal_max = fields.Integer(string=u"Número máximo")

    gov_active = fields.Boolean("Activo")
    gov_sequence_id = fields.Many2one("ir.sequence", string=u"Gubernamental")
    gov_number_next_actual = fields.Integer(string=u"Próximo número", related="gov_sequence_id.number_next_actual")
    gov_max = fields.Integer(string=u"Número máximo")

    special_active = fields.Boolean("Activo")
    special_sequence_id = fields.Many2one("ir.sequence", string=u"Especiales")
    special_number_next_actual = fields.Integer(string=u"Próximo número",
                                                related="special_sequence_id.number_next_actual")
    special_max = fields.Integer(string=u"Número máximo")

    unico_active = fields.Boolean("Activo")
    unico_sequence_id = fields.Many2one("ir.sequence", string=u"Especiales")
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

    user_ids = fields.Many2many("res.users", string=u"Usuarios que pueden usar estas secuancias")

    _sql_constraints = [
        ('shop_ncf_config_name_uniq', 'unique(name, company_id)', u'El Prefijo NCF de la sucursal debe de ser unico!'),
    ]

    @api.onchange("name")
    def onchange_name(self):
        if self.name:
            if self.final_sequence_id:
                self.final_sequence_id.write({"prefix": self.name+"02",
                                              "name": "Facturas de cliente final {}".format(self.name)})
                self.fiscal_sequence_id.write({"prefix": self.name+"01",
                                              "name": "Facturas de cliente fiscal {}".format(self.name)})
                self.gov_sequence_id.write({"prefix": self.name+"15",
                                              "name": "Facturas de cliente gubernamental {}".format(self.name)})
                self.special_sequence_id.write({"prefix": self.name+"14",
                                              "name": "Facturas de cliente especiales {}".format(self.name)})
                self.unico_sequence_id.write({"prefix": self.name+"12",
                                              "name": "Facturas de unico ingreso {}".format(self.name)})
                self.nc_sequence_id.write({"prefix": self.name+"04",
                                              "name": "Notas de credito {}".format(self.name)})
                self.nd_sequence_id.write({"prefix": self.name+"03",
                                              "name": "Notas de debito {}".format(self.name)})
            else:
		import ipdb;ipdb.set_trace()
                self.setup_ncf(name=self.name,company_id=self.company_id.id, journal_id=self.journal_id.id,shop_id=self)




    @api.model
    def get_user_shop_config(self):
        user_shops = self.search([('user_ids', '=', self._uid)])
        if not user_shops:
            raise exceptions.UserError("Su usuario no tiene una sucursal asignada.")
        return user_shops[0]

    @api.model
    def setup_ncf(self, name=False, company_id=False, journal_id=False, user_id=False, shop_id=False):
	journal_obj = self.env['account.journal']
        special_position_id = self.env.ref("ncf_manager.ncf_manager_special_fiscal_position")
        self.env["account.fiscal.position"].search([('id','!=',special_position_id.id)]).unlink()

        name = name or u"A01001001"
        company_id = company_id or self.env.user.company_id.id
	journal_names = ['Customer Invoices', 'Facturas de Clientes']
        journal_id = journal_id or journal_obj.search([('type', '=', 'sale'), ('name', 'in', journal_names)]).id
        self.env["account.journal"].sudo().browse(journal_id).write({"ncf_control": True})

        user_id = user_id or 1

        final_prefix = name + u"02"
        fiscal_prefix = name + u"01"
        gov_prefix = name + u"15"
        esp_prefix = name + u"14"
        nc_prefix = name + u"04"
        nd_prefix = name + u"03"
        unico_prefix = name + u"12"

        if self.search_count([('company_id','=',company_id),('name','=',name)]) == 0:
            if shop_id:
                shop = shop_id
            else:
                shop = self.create({"name": name,
                                    "journal_id": journal_id,
                                    "user_ids": [(4, user_id, False)],
                                    "company_id": company_id,
                                    u'final_max': 10000000,
                                    u'fiscal_max': 10000000,
                                    u'gov_max': 10000000,
                                    u'special_max': 10000000,
                                    u'nc_max': 10000000,
                                    u'nd_max': 10000000,
                                    u'unico_max': 10000000
                                    })

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
                          u'suffix': False
                          }

            sale_journal = self.env["account.journal"].browse(journal_id)
            sale_journal.ncf_control = True

            seq_values["prefix"] = final_prefix
            seq_values["name"] = "Facturas de cliente final {}".format(name)
            final_id = self.env["ir.sequence"].create(seq_values)
            shop.final_sequence_id = final_id.id

            seq_values["prefix"] = fiscal_prefix
            seq_values["name"] = "Facturas de cliente fiscal {}".format(name)
            fiscal_id = self.env["ir.sequence"].create(seq_values)
            shop.fiscal_sequence_id = fiscal_id.id

            seq_values["prefix"] = gov_prefix
            seq_values["name"] = "Facturas de cliente gubernamental {}".format(name)
            gov_id = self.env["ir.sequence"].create(seq_values)
            shop.gov_sequence_id = gov_id.id

            seq_values["prefix"] = esp_prefix
            seq_values["name"] = "Facturas de cliente especiales {}".format(name)
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
            message = u"La secuencia para el tipo de NCF las notas de crédito para el punto de venta {} a sobrepasado el " \
                      u"número maximo solicitado debe solicitar mas NCF para este punto de venta".format(self.name)
        elif sale_fiscal_type == "final" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"La secuencia para el tipo de NCF consumidor final para el punto de venta {} a sobrepasado el " \
                      u"número maximo solicitado debe solicitar mas NCF para este punto de venta".format(self.name)
        elif sale_fiscal_type == "fiscal" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"La secuencia para el tipo de NCF cr´ito fiscal para el punto de venta {} a sobrepasado el " \
                      u"número maximo solicitado debe solicitar mas NCF para este punto de venta".format(self.name)
        elif sale_fiscal_type == "gov" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"La secuencia para el tipo de NCF gubernamental para el punto de venta {} a sobrepasado el " \
                      u"número maximo solicitado debe solicitar mas NCF para este punto de venta".format(self.name)
        elif sale_fiscal_type == "special" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"La secuencia para el tipo de NCF régimenes especiales para el punto de venta {} a sobrepasado el " \
                      u"número maximo solicitado debe solicitar mas NCF para este punto de venta".format(self.name)
        elif sale_fiscal_type == "unico" and self.final_max >= self.final_sequence_id.number_next_actual - 10:
            message = u"La secuencia para el tipo de NCF único ingreso para el punto de venta {} a sobrepasado el " \
                      u"número maximo solicitado debe solicitar mas NCF para este punto de venta".format(self.name)


            invoice.message_post(body=message)

