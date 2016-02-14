# -*- coding: utf-8 -*-

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

