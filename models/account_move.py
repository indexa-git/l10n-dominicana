# -*- coding: utf-8 -*-
########################################################################################################################
#  Copyright (c) 2015 - Marcos Organizador de Negocios SRL. (<https://marcos.do/>) #  Write by Eneldo Serrata (eneldo@marcos.do)
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
from openerp import models, api, _, fields
from openerp.exceptions import UserError
import openerp.addons.decimal_precision as dp


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        invoice = self._context.get('invoice', False)
        self._post_validate()
        for move in self:
            move.line_ids.create_analytic_lines()
            if move.name == '/':
                new_name = False
                journal = move.journal_id
                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                elif invoice and invoice.type == 'out_invoice':
                    fiscal_type = invoice.fiscal_position_id.client_fiscal_type
                    if fiscal_type == 'fiscal':
                        sequence = journal.fiscal_sequence_id
                    elif fiscal_type == 'gov':
                        sequence = journal.gov_sequence_id
                    elif fiscal_type == 'special':
                        sequence = journal.special_sequence_id
                    elif fiscal_type == 'unico':
                        sequence = journal.unique_sequence_id
                    else:
                        sequence = journal.final_sequence_id

                    new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()

                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            sequence = journal.refund_sequence_id
                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))

                if new_name:
                    move.name = new_name
        return self.write({'state': 'posted'})


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.one
    @api.depends('debit','credit')
    def _bal(self):
        self.net = self.debit-self.credit

    net = fields.Float("Balance", compute=_bal, digits=dp.get_precision('Account'), store=True)

