# -*- coding: utf-8 -*-

from openerp import models, api, fields


class CheckCashBox(models.TransientModel):
    _name = "check.cash.box"


    dummy = fields.Boolean()

    @api.model
    def confirm_cash_diff(self):
        pass
        # import pdb;pdb.set_trace()