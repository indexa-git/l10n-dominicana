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
from odoo import models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        invoice = self._context.get('invoice', False)

        if invoice and invoice.journal_id.ncf_control:
            if not invoice.journal_id.ncf_ready:
                raise UserError(_("Debe configurar los NCF para este diario."))
            if invoice.type == "out_invoice":
                if invoice.is_nd:
                    return super(AccountMove, self.with_context(sale_fiscal_type="debit_note")).post()
                else:
                    return super(AccountMove, self.with_context(sale_fiscal_type=invoice.sale_fiscal_type)).post()
            elif invoice.type == "out_refund":
                return super(AccountMove, self.with_context(sale_fiscal_type="credit_note")).post()
        else:
            return super(AccountMove, self).post()
