# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2015 Marcos Organizador de Negocios SRL http://marcos.do
#    Write by Eneldo Serrata (eneldo@marcos.do)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class stock_inventory(models.Model):
    _inherit = "stock.inventory"

    @api.multi
    def _selection_filter(self):
        res = super(stock_inventory, self)._selection_filter()

        mode_to_add = [("invenory_plus", "Importar desde los codigos y sumar al inventario actual"),
                       ("inventory_update", "Importar desde los codigos y actualizar el inventario actual")
                       ]
        res += mode_to_add

        return res

    filter = fields.Selection(_selection_filter, 'Inventory of', required=True,
                              help="If you do an entire inventory, you can choose 'All Products' and it will prefill the inventory with the current stock.  If you only do some products  " \
                                   "(e.g. Cycle Counting) you can choose 'Manual Selection of Products' and the system won't propose anything.  You can also let the " \
                                   "system propose for a single product / lot /... ")

    @api.multi
    def action_start(self):
        for inventory in self:
            lines = []
            vals = {'state': 'confirm', 'date': fields.Datetime.now()}
            if (inventory.filter != 'partial') and not inventory.line_ids:
                lines = [line_values for line_values in inventory._get_inventory_lines_values()]

            for line in lines:
                if not line.get("theoretical_qty", False):
                    line.update({"theoretical_qty": 0.0})
                if not line.get("prod_lot_id", False):
                    line.update({"prod_lot_id": False})
                if not line.get("package_id", False):
                    line.update({"package_id": False})
                if not line.get("product_qty", False):
                    line.update({"product_qty": 0.0})
                if not line.get("product_uom_id", False):
                    line.update({"product_uom_id": 1})
                if not line.get("partner_id", False):
                    line.update({"partner_id": False})
                line.update({"inventory_id": self.id})
                values = [x if x else None for x in line.values()]
                placeholder = ", ".join(["%s"] * len(line.keys()))
                stmt = "INSERT INTO {table} ({columns}) VALUES ({values}) RETURNING id;".format(
                    table="stock_inventory_line", columns='"' + '","'.join(line.keys()) + '"', values=placeholder)

                self.env.cr.execute(stmt, values)

            self.write(vals)

        return True

    def prepare_inventory(self):
        if self.filter in ["invenory_plus", "inventory_update"]:
            return self.write({'state': 'confirm', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        else:
            return self.action_start()
            # return super(stock_inventory, self).action_start()

    @api.multi
    def update_cost_on_product_from_stock_move(self):
        product_ids = self.env["product.product"].search([])
        for product_id in product_ids:
            stock_move = self.env["stock.move"].search([('product_id', '=', product_id.id), ('location_id', '=', 8)])
            if stock_move:
                qty = 0
                cost = 0
                for move in stock_move:
                    qty += move.product_uom_qty
                    cost += move.product_uom_qty * move.price_unit

                if qty and cost:
                    cost = cost / qty
                else:
                    cost = 0

                property = self.env["ir.property"].search([('res_id','=',"product.product,"+str(product_id.id)),
                                                           ('name','=','standard_price')])
                if property:
                    property.write({"value_float": cost})
                else:
                    self.env["ir.property"].create({"name": "standard_price",
                                                    "company_id": 1,
                                                    "fields_id": 2128,
                                                    "res_id": "product.product,"+str(product_id.id),
                                                    "value_float": cost,
                                                    "type": "float"})


