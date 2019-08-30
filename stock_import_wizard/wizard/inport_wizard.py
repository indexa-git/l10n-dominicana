# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013-2015 Marcos Organizador de Negocios SRL http://marcos.do
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
from odoo import models, api, fields, exceptions


class invetory_import(models.TransientModel):
    _name = "invetory.import"

    ref_list = fields.Text("lista de referencia del producto")
    ref_lines = fields.One2many("invetory.import.lines", "inventory_id")
    to_consider_forecast = fields.Boolean("Incluir pronostico")

    @api.multi
    def import_product_ref(self):
        error_list = []
        context = self.env.context

        ref_sum_dict = {}
        if not context.get("qty", False):
            ref_list = self.ref_list.split("\n")

        inventory_record = self.env[self._context["active_model"]].browse(self._context["active_id"])
        inventory_record.action_reset_product_qty()
        invalid_key = []

        if context.get("qty", False):
            for line in self.ref_lines:
                default_code, qty = line.ref_item, line.qty

                if not ref_sum_dict.get(default_code, False):
                    ref_sum_dict[default_code] = qty
                else:
                    ref_sum_dict[default_code] += qty
        else:
            for ref in ref_list:
                if "\t" in ref:
                    ref_list = ref.split("\t")
                    default_code = ref_list[0]
                    qty = ref_list[1]
                    qty = float(qty)
                elif len(ref.split()) > 1:
                    ref_list = ref.split()
                    default_code = ref_list[0]
                    qty = ref_list[1]
                    qty = float(qty)
                else:
                    default_code, qty = ref, 1.00

                if not ref_sum_dict.get(ref, False):
                    ref_sum_dict[default_code] = qty
                else:
                    ref_sum_dict[default_code] += qty

        for key, value in ref_sum_dict.items():

            key = key.strip()
            if not key == '':
                product_obj = self.env["product.product"].search([('default_code', '=', key)])
                tipo = "la referencia interna"

                if not product_obj:
                    product_obj = self.env["product.product"].search([('barcode', '=', key)])
                    tipo = "el mismo codigo de barra"

                if not product_obj:
                    product_obj = self.env["product.product"].search([('supplier_barcode', '=', key)])
                    tipo = "el mismo codigo de barra del suplidor"

                if product_obj.exists():
                    if len(product_obj) > 1:
                        raise exceptions.ValidationError("Existen mas de un producto con {} {}".format(tipo,key))
                    product_in_line = inventory_record.line_ids.filtered(
                        lambda x, p=product_obj.id: x.product_id.id == p)

                    if len(product_obj) > 1:
                        duplicate = [prod.name for prod in product_obj]
                        error_list.append(u"Hay varios productos con el mismo codigo de barra - {}".format(duplicate))
                    elif product_obj.standard_price <= 0:
                        error_list.append(u"Debe corregir el costo para este productos - [{}]{}".format(
                            product_obj.default_code or product_obj.barcode,
                            product_obj.name))
                    new_qty = float(value)
                    if self.to_consider_forecast:
                        new_qty += product_obj.outgoing_qty
                    if not product_in_line.exists():
                        vals = {'inventory_id': inventory_record.id,
                                'location_id': inventory_record.location_id.id,
                                'package_id': False,
                                'partner_id': False,
                                'prod_lot_id': False,
                                'product_id': product_obj.id,
                                'product_qty': new_qty,
                                'product_uom_id': product_obj.product_tmpl_id.uom_po_id.id}
                        self.env["stock.inventory.line"].create(vals)
                    else:
                        product_in_line.write({"product_qty": new_qty})
                else:
                    if key not in invalid_key:
                        invalid_key.append(key)
                        error_list.append(u"A introducido una código de barra no valido > {}".format(key))

        if error_list:
            error_list_msg = ""
            for error in error_list:
                error_list_msg += error + "\n"
            raise exceptions.ValidationError(error_list_msg)
        else:

            vals = inventory_record._get_inventory_lines_values()
            for line in inventory_record.line_ids:
                for key in vals:
                    if key["product_id"] == line.product_id.id:
                        line.theoretical_qty = key["theoretical_qty"]
                        if inventory_record.filter == "invenory_plus":
                            line.product_qty += key["theoretical_qty"]

            return True


class invetory_import(models.TransientModel):
    _name = "invetory.import.lines"

    inventory_id = fields.Many2one("invetory.import")
    ref_item = fields.Char("Referencia", required=True)
    qty = fields.Float("Cantidad", required=True)
