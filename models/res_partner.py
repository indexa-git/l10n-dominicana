# -*- coding: utf-8 -*-

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    journal_id = fields.Many2one("account.journal", "Diario de compra")