# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>
#             Manuel Marquez <buzondemam@gmail.com>

# This file is part of NCF Purchase

# NCF Purchase is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Purchase is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('partner_id')
    def onchange_partnerid(self):

        if self.partner_id and self.type == 'in_invoice':
            if self.partner_id.purchase_journal_id:
                self.journal_id = self.partner_id.purchase_journal_id

        elif self.type == 'in_invoice' and \
                self.env.context.get('default_purchase_id'):
            purchase_order = self.env['purchase.order']
            po = purchase_order.browse(
                self.env.context.get('default_purchase_id'))
            supplier = po.partner_id
            if supplier.purchase_journal_id:
                self.journal_id = supplier.purchase_journal_id
