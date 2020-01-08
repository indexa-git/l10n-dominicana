# © 2018 Yasmany Castillo <yasmany003@gmail.com>

import logging

from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order.
         This method may be overridden to implement custom invoice generation
         (making sure to call super() to establish a clean extension chain).
        """
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        partner_id = self.partner_id
        partner_fiscal_type_id = partner_id.sale_fiscal_type_id
        journal_id = self.env['account.journal'].browse(
            invoice_vals['journal_id'])

        if not journal_id.l10n_do_fiscal_journal:
            return invoice_vals

        elif not partner_fiscal_type_id:
            prefix = 'B01' if partner_id.vat else 'B02'
            fiscal_type = self.env[
                'account.fiscal.type'].search([
                    ('type', '=', 'out_invoice'),
                    ('prefix', '=', prefix),
                ], limit=1)
            if not fiscal_type:
                raise ValidationError(
                    _("There's not a fiscal type for prefix {}, please create "
                      "it.").format(prefix))
            invoice_vals['fiscal_type_id'] = fiscal_type.id

        elif partner_id.parent_id and partner_id.parent_id.is_company \
                and partner_id.parent_id.sale_fiscal_type_id:
            invoice_vals['fiscal_type_id'] = \
                partner_id.parent_id.sale_fiscal_type_id.id

        else:
            invoice_vals['fiscal_type_id'] = partner_fiscal_type_id.id

        return invoice_vals
