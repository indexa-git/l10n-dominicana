# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    related = fields.Selection([('0', 'Not Related'), ('1', 'Related')], default='0')

    @api.onchange('country_id')
    def _onchage_country_id(self):
        if self.country_id:
            self.related = '0'
