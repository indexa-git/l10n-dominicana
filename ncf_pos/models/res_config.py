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

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval


class PosConfiguration(models.TransientModel):
    _inherit = 'pos.config.settings'

    pos_session_concile_type = fields.Selection([('session', u'Por session'), ('none', u'Manual')],
                                                string=u"Conciliación", default=u"session")
    pos_session_picking_on_cron = fields.Boolean("Crear conduce desde un cron", default=False)

    @api.model
    def get_default_pos_session_concile_type(self, fields):
        IrConfigParam = self.env['ir.config_parameter']
        try:
            return {
                'pos_session_concile_type': safe_eval(
                    IrConfigParam.get_param('ncf_pos.pos_session_concile_type', 'session'))
            }
        except:
            return {
                'pos_session_concile_type': 'session'
            }

    @api.multi
    def set_pos_session_concile_type(self):
        self.ensure_one()
        IrConfigParam = self.env['ir.config_parameter']
        IrConfigParam.set_param('ncf_pos.pos_session_concile_type', repr(self.pos_session_concile_type))

    @api.model
    def get_default_pos_session_picking_on_cron(self, fields):
        IrConfigParam = self.env['ir.config_parameter']
        return {
            'pos_session_picking_on_cron': safe_eval(
                IrConfigParam.get_param('ncf_pos.pos_session_picking_on_cron', 'False'))
        }

    @api.multi
    def set_pos_session_picking_on_cron(self):
        self.ensure_one()
        IrConfigParam = self.env['ir.config_parameter']
        IrConfigParam.set_param('ncf_pos.pos_session_picking_on_cron', repr(self.pos_session_picking_on_cron))
