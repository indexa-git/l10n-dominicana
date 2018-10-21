# © 2018 Yasmany Castillo <yasmany003@gmail.com>

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
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import ncf
except(ImportError, IOError) as err:
    _logger.debug(err)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        partner_id = self.partner_id
        sale_fiscal_type = partner_id.sale_fiscal_type

        if partner_id.parent_id and partner_id.parent_id.is_company:
            invoice_vals[
                'sale_fiscal_type'] = partner_id.parent_id.sale_fiscal_type
        elif not sale_fiscal_type and partner_id.vat and partner_id.is_company:
            invoice_vals['sale_fiscal_type'] = 'fiscal'
        else:
            invoice_vals['sale_fiscal_type'] = sale_fiscal_type

        return invoice_vals
