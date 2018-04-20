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


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.depends("ncf_control")
    @api.one
    def check_ncf_ready(self):
        self.ncf_ready = len(self.date_range_ids) > 1

    purchase_type = fields.Selection(
        [("normal", "Compras Fiscales"),
         ("minor", "Gastos Menores"),
         ("informal", "Registro de Proveedores Informales"),
         ("exterior", "Compras al Exterior"),
         ("import", "Importaciones"),
         ("others", "No deducibles. No requiere NCF")],
        string="Tipo de Compra", default="others")

    payment_form = fields.Selection(
        [("cash", "Efectivo"),
         ("bank", u"Cheque / Transferencia / Depósito"),
         ("card", u"Tarjeta Crédito / Débito"),
         ("credit", u"A Crédito"),
         ("swap", "Permuta"),
         ("bond", "Bonos o Certificados de Regalo"),
         ("others", "Otras Formas de Venta")],
        string="Forma de Pago", oldname="ipf_payment_type")

    ncf_remote_validation = fields.Boolean("Validar con DGII", default=False)

    ncf_control = fields.Boolean(related="sequence_id.ncf_control")
    prefix = fields.Char(related="sequence_id.prefix")
    date_range_ids = fields.One2many(related="sequence_id.date_range_ids")
    ncf_ready = fields.Boolean(compute=check_ncf_ready)
    special_fiscal_position_id = fields.Many2one("account.fiscal.position", string=u"Posición fiscal para regímenes especiales.",
                                                 help=u"Define la posición fiscal por defecto para los clientes que tienen definido el tipo de comprobante fiscal regímenes especiales.")

    @api.onchange("type")
    def onchange_type(self):
        if self.type != 'sale':
            self.ncf_control = False

    @api.multi
    def create_ncf_sequence(self):
        if self.ncf_control and len(self.sequence_id.date_range_ids) == 1:
            # this method read Selection values from res.partner sale_fiscal_type fields
            selection = self.env["ir.sequence.date_range"].get_sale_fiscal_type_from_partner()
            for sale_fiscal_type in selection:
                self.sequence_id.date_range_ids[0].copy({'sale_fiscal_type': sale_fiscal_type[0]})

            self.sequence_id.date_range_ids.invalidate_cache()
            self.sequence_id.write({'prefix': 'B', 'padding': 8})


class AccountTax(models.Model):
    _inherit = 'account.tax'

    purchase_tax_type = fields.Selection(
        [('itbis', 'ITBIS Pagado'),
         ('ritbis', 'ITBIS Retenido'),
         ('isr', 'ISR Retenido'),
         ('rext', 'Remesas al Exterior (Ley 253-12)'),
         ('none', 'No Deducible')],
        default="none", string="Tipo de Impuesto en Compra"
    )

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
