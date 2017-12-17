# -*- coding: utf-8 -*-
###############################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL.
#  (<https://marcos.do/>)

#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it,
# unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without
# copying any source code or material from the Software. You may distribute
# those modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Softwar or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

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
            if invoice and invoice.type == 'out_invoice' and not invoice.journal_id.ncf_control:
                return super(AccountMove, self).post()

            if invoice and invoice.type == 'out_invoice' and invoice.journal_id.ncf_control:
                if not invoice.sale_fiscal_type:
                    return super(AccountMove, self).post()

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
    base_it1_cels = fields.Char("Celdas de la base para el IT-1")
    tax_it1_cels = fields.Char("Celdas del inpuesto para el IT-1")
    base_ir17_cels = fields.Char("Celdas de la base para el IR-17")
    tax_ir17_cels = fields.Char("Celdas del inpuesto para el IR-17")
