# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>)
#  Write by Eneldo Serrata (eneldo@marcos.do)
#  See LICENSE file for full copyright and licensing details.
#
# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used
# (nobody can redistribute (or sell) your module once they have bought it, unless you gave them your consent)
# if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
########################################################################################################################

from odoo import models, fields, api, exceptions


class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_partner_id = fields.Many2one("res.partner", string=u"Cliente de contado", required=True)
    load_orders_of_current_session = fields.Boolean(string=u'Cargar orden de sesión actual sólo', default=True)
    load_orders_after_this_date = fields.Boolean(string=u'Cargar orden después de una fecha especificada')
    load_orders_from = fields.Date(string=u'Seleccione una fecha')

    @api.onchange('load_orders_of_current_session')
    def onchange_load_orders_of_current_session(self):
        if self.load_orders_of_current_session:
            self.load_orders_after_this_date = False;

    @api.onchange("load_orders_after_this_date")
    def onchange_load_orders_after_this_date(self):
        if self.load_orders_after_this_date:
            self.load_orders_of_current_session = False;

    @api.constrains('load_orders_after_this_date')
    def load_orders_date_validation(self):
        if self.load_orders_after_this_date:
            if not self.load_orders_from:
                raise exceptions.ValidationError(u"¡Por favor especifique una fecha!")

