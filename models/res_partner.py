# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

from lxml import etree


class ResPartner(models.Model):
    _inherit = "res.partner"


    journal_id = fields.Many2one("account.journal", "Diario de compra", domain=[('type','=','purchase')])
    property_account_position_supplier_id = fields.Many2one('account.fiscal.position', company_dependent=True,
        string=_("Supplier Fiscal Position"), domain=[('supplier','=',True)],
        help="The fiscal position will determine taxes and accounts used for the supplier.", oldname="property_account_position")
    property_account_position_id = fields.Many2one('account.fiscal.position', company_dependent=True,
        string=_("Customer Fiscal Position"),
        help="The fiscal position will determine taxes and accounts used for the Customer.", oldname="property_account_position",
                                                   domain=[('supplier','=',False)])