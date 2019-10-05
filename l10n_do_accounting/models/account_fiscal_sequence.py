# © 2019 José López <jlopez@indexa.do>

import pytz
from datetime import datetime

from odoo import models, fields, api, _


def get_l10n_do_datetime():
    """
    Multipurpose Dominican Republic local datetime
    """

    # *-*-*-*-*- Remove this comment *-*-*-*-*-*
    # Because an user can use a distinct timezone,
    # this method ensure that DR localtime stuff like
    # auto expire Fiscal Sequence by its date works,
    # no matter server/client date.

    date_now = datetime.now()
    return pytz.timezone('America/Santo_Domingo').localize(date_now)


class AccountFiscalSequence(models.Model):
    _name = 'account.fiscal.sequence'
    _description = "Account Fiscal Sequence"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Authorization number",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )
    expiration_date = fields.Date(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )
    fiscal_type_id = fields.Many2one(
        'account.fiscal.type',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )
    type = fields.Selection(
        related='fiscal_type_id.type',
        store=True,
    )
    sequence_start = fields.Integer(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )
    sequence_end = fields.Integer(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        string="Internal Sequence",
    )
    warning_gap = fields.Integer()
    number_next_actual = fields.Integer(
        string='Next Number',
        help="Next number of this sequence",
        related='sequence_id.number_next_actual',
    )
    next_fiscal_number = fields.Char(
        compute='_compute_next_fiscal_number',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('active', 'Active'),
        ('depleted', 'Depleted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ],
        default='draft',
        track_visibility='onchange',
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )

    @api.multi
    @api.depends('fiscal_type_id.prefix', 'sequence_id.padding', 'sequence_id.number_next_actual')
    def _compute_next_fiscal_number(self):
        for seq in self:
            seq.next_fiscal_number = "%s%s" % (
                seq.fiscal_type_id.prefix,
                str(seq.sequence_id.number_next_actual).zfill(seq.sequence_id.padding))

    @api.multi
    def action_view_sequence(self):
        self.ensure_one()
        sequence_id = self.sequence_id
        action = self.env.ref('base.ir_sequence_form').read()[0]
        if sequence_id:
            action['views'] = [(self.env.ref('base.sequence_view').id, 'form')]
            action['res_id'] = sequence_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        msg = _('Are you sure want to confirm this Fiscal Sequence? '
                'Once you confirm this Fiscal Sequence cannot be edited.')
        action = self.env.ref('l10n_do_accounting.account_fiscal_sequence_validate_wizard_action').read()[0]
        action['context'] = {'default_name': msg, 'default_fiscal_sequence_id': self.id, 'action': 'confirm'}
        return action

    @api.multi
    def _action_confirm(self):
        for rec in self:

            # Use DR local time
            l10n_do_date = get_l10n_do_datetime().date()

            if l10n_do_date >= rec.expiration_date:
                rec.state = 'expired'
            else:
                # Creates a new sequence of this Fiscal Sequence
                sequence_id = self.env['ir.sequence'].create({
                    'name': _('%s %s Sequence') % (rec.fiscal_type_id.name, rec.name[-9:]),
                    'implementation': 'standard',
                    'padding': 8,
                    'number_increment': 1,
                    'number_next_actual': rec.sequence_start,
                    'number_next': rec.sequence_start,
                    'use_date_range': False,
                    'company_id': rec.company_id.id,
                })
                rec.write({
                    'state': 'active',
                    'sequence_id': sequence_id.id,
                })

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        msg = _('Are you sure want to cancel this Fiscal Sequence? '
                'Once you cancel this Fiscal Sequence cannot be used.')
        action = self.env.ref('l10n_do_accounting.account_fiscal_sequence_validate_wizard_action').read()[0]
        action['context'] = {'default_name': msg, 'default_fiscal_sequence_id': self.id, 'action': 'cancel'}
        return action

    @api.multi
    def _action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            if rec.sequence_id:
                # *-*-*-*-*- Remove this comment *-*-*-*-*-*
                # Preserve internal sequence just for audit purpose.
                rec.sequence_id.active = False

    @api.multi
    def name_get(self):
        result = []
        for sequence in self:
            result.append((sequence.id, "%s - %s" % (sequence.name, sequence.fiscal_type_id.name)))
        return result


class AccountFiscalType(models.Model):
    _name = 'account.fiscal.type'
    _description = "Account Fiscal Type"

    name = fields.Char(
        required=True,
        copy=False,
    )
    prefix = fields.Char(
        copy=False,
    )
    type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
    ],
        required=True,
    )
    fiscal_position_id = fields.Many2one(
        "account.fiscal.position",
        string="Fiscal Position",
    )
    internal_generate = fields.Boolean(
        default=True,
    )
