# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.models import AbstractModel


# class publisher_warranty_contract(AbstractModel):
#     _inherit = "publisher_warranty.contract"
#
#     def _get_message(self, cr, uid):
#         msg = super(publisher_warranty_contract, self)._get_message(cr, uid)
#
#         if msg =="48ecc273-c82c-11e5-9118-6c4008b3134c":
#             print "_get_message============="
#             print self._context
#         return msg


class ir_config_parameter(osv.osv):
    _inherit = "ir.config_parameter"

    def get_param(self, cr, uid, key, default=False, context=None):
        res = super(ir_config_parameter, self).get_param(cr, uid, key, default=default, context=context)
        if key =="database.uuid":
            return

        return res
