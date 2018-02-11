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
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    purchase_type = fields.Selection(
        [("normal", "Requiere NCF"),
         ("minor", "Gasto Menor. NCF Generado por el Sistema"),
         ("informal", "Proveedores Informales. NCF Generado por el Sistema"),
         ("exterior", "Pagos al Exterior. NCF Generado por el Sistema"),
         ("import", "Importaciones. NCF Generado por el Sistema"),
         ("others", "Otros. No requiere NCF")],
        string="Tipo de Compra", default="others")

    ncf_control = fields.Boolean("Control de NCF", default=False)
    ncf_remote_validation = fields.Boolean("Validar con DGII", default=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        invoice = self._context.get('invoice', False)
        self._post_validate()
        for move in self:
            if invoice and invoice.type in ['out_invoice', 'out_refund'] and invoice.journal_id.ncf_control:

                if invoice.type == 'out_invoice' and not invoice.sale_fiscal_type:
                    raise ValidationError("Debe especificar el tipo de"
                                          " comprobante para la venta.")

                if not invoice.move_name:
                    active_sequence = False
                    if invoice.is_nd:
                        sequence = invoice.shop_id.nd_sequence_id
                        active_sequence = invoice.shop_id.nd_active
                    elif invoice.type == "out_refund":
                        sequence = invoice.shop_id.nc_sequence_id
                        active_sequence = invoice.shop_id.nc_active
                    elif invoice.sale_fiscal_type == "final":
                        sequence = invoice.shop_id.final_sequence_id
                        active_sequence = invoice.shop_id.final_active
                    elif invoice.sale_fiscal_type == "fiscal":
                        sequence = invoice.shop_id.fiscal_sequence_id
                        active_sequence = invoice.shop_id.fiscal_active
                    elif invoice.sale_fiscal_type == "gov":
                        sequence = invoice.shop_id.gov_sequence_id
                        active_sequence = invoice.shop_id.gov_active
                    elif invoice.sale_fiscal_type == "special":
                        sequence = invoice.shop_id.special_sequence_id
                        active_sequence = invoice.shop_id.special_active
                    elif invoice.sale_fiscal_type == "unico":
                        sequence = invoice.shop_id.special_sequence_id
                        active_sequence = invoice.shop_id.special_active

                    if not active_sequence:
                        raise ValidationError(u"Los NCF para **{}** no están activados.".format(invoice.sale_fiscal_type))

                    invoice.shop_id.check_max(invoice.sale_fiscal_type,
                                              invoice)
                    invoice.move_name = sequence.with_context(ir_sequence_date=invoice.date_invoice).next_by_id()
                    invoice.reference = invoice.journal_id.sequence_id.with_context(ir_sequence_date=invoice.date_invoice).next_by_id()

        return super(AccountMove, self).post()


class AccountTax(models.Model):
    _inherit = 'account.tax'

    purchase_tax_type = fields.Selection(
        [('itbis', 'ITBIS Pagado'),
         ('ritbis', 'ITBIS Retenido'),
         ('isr', 'ISR Retenido'),
         ('rext', 'Remesas al Exterior (Ley  253-12)'),
         ('none', 'No Deducible')],
        default="none", string="Tipo de Impuesto de Compra"
    )
