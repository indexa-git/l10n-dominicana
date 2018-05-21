# -*- coding: utf-8 -*-
from odoo import models, fields


class PosSearchCriteria(models.Model):
    _name = "pos.search_criteria"

    name = fields.Char("Name")
    criteria = fields.Char("Criteria")
