# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ResUser(models.Model):
    _inherit = 'res.users'


    pos_security_pin = fields.Char('Security PIN',size=32, help='A Security PIN used to protect sensible functionality in the Point of Sale')

    _sql_constraints = [
        ('unique_pos_security_pin', 'unique (pos_security_pin)', 'El pin digitado debe de ser unico en el sistema.')
    ]