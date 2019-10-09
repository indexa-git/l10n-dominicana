# © 2019 José López <jlopez@indexa.do>
# © 2019 Raul Ovalle <rovalle@guavana.com>

import pytz
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
        default=datetime.strptime(str(int(str(fields.Date.today())[0:4])+1)+'-12-31', '%Y-%m-%d').date()
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
        default=1,
        copy=False,
    )
    sequence_end = fields.Integer(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
        default=1,
        copy=False,
    )
    sequence_remaining = fields.Integer(
        string='Remaining',
        compute='_compute_sequence_remaining',
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        string="Internal Sequence",
        copy=False,
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
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )

    @api.multi
    @api.depends('sequence_end', 'sequence_id.number_next')
    def _compute_sequence_remaining(self):
        for rec in self:
            if rec.sequence_id:
                next_number = rec.sequence_id.number_next_actual + 1
                remaining = rec.sequence_end - next_number
                rec.sequence_remaining = remaining

    @api.multi
    @api.depends('fiscal_type_id.prefix', 'sequence_id.padding',
                 'sequence_id.number_next_actual')
    def _compute_next_fiscal_number(self):
        for seq in self:
            seq.next_fiscal_number = "%s%s" % (
                seq.fiscal_type_id.prefix,
                str(seq.sequence_id.number_next_actual).zfill(
                    seq.sequence_id.padding))

    @api.constrains('fiscal_type_id', 'state')
    def _validate_unique_active_type(self):
        """
        Validate an active sequence type uniqueness
        """
        domain = [
            ('state', '=', 'active'),
            ('fiscal_type_id', '=', self.fiscal_type_id.id),
            ('company_id', '=', self.company_id.id),
        ]
        if self.search_count(domain) > 1:
            raise ValidationError(
                _("Another sequence is active for this type."))

    @api.multi
    @api.constrains('sequence_start', 'sequence_end', 'state',
                    'fiscal_type_id')
    def _validate_sequence_range(self):
        for rec in self.filtered(lambda s: s.state != 'cancelled'):
            if any([True for value in [rec.sequence_start, rec.sequence_end]
                    if value <= 0]):
                raise ValidationError(
                    _('Sequence values must be greater than zero.'))
            if rec.sequence_start >= rec.sequence_end:
                raise ValidationError(
                    _('End sequence must be greater than start sequence.'))
            domain = [
                ('sequence_end', '<=', rec.sequence_start),
                ('fiscal_type_id', '=', rec.fiscal_type_id.id),
                ('state', 'not in', ('draft', 'cancelled', 'queue')),
                ('company_id', '=', rec.company_id.id),
            ]
            if self.search_count(domain) > 1:
                raise ValidationError(
                    _("You cannot use another Fiscal Sequence range."))

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.sequence_id:
                rec.sequence_id.sudo().unlink()
        return super(AccountFiscalSequence, self).unlink()

    @api.multi
    def name_get(self):
        result = []
        for sequence in self:
            result.append((sequence.id, "%s - %s" % (
                sequence.name, sequence.fiscal_type_id.name)))
        return result

    @api.multi
    def action_view_sequence(self):
        self.ensure_one()
        sequence_id = self.sequence_id
        action = self.env.ref('base.ir_sequence_form').read()[0]
        if sequence_id:
            action['views'] = [
                (self.env.ref('base.sequence_view').id, 'form')]
            action['res_id'] = sequence_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        msg = _('Are you sure want to confirm this Fiscal Sequence? '
                'Once you confirm this Fiscal Sequence cannot be edited.')
        action = self.env.ref(
            'l10n_do_accounting.account_fiscal_sequence_validate_wizard_action'
        ).read()[0]
        action['context'] = {'default_name': msg,
                             'default_fiscal_sequence_id': self.id,
                             'action': 'confirm'}
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
                    'name': _('%s %s Sequence') % (rec.fiscal_type_id.name,
                                                   rec.name[-9:]),
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
        action = self.env.ref(
            'l10n_do_accounting.account_fiscal_sequence_validate_wizard_action'
        ).read()[0]
        action['context'] = {'default_name': msg,
                             'default_fiscal_sequence_id': self.id,
                             'action': 'cancel'}
        return action

    @api.multi
    def _action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            if rec.sequence_id:
                # *-*-*-*-*- Remove this comment *-*-*-*-*-*
                # Preserve internal sequence just for audit purpose.
                rec.sequence_id.active = False

    def _expire_sequences(self):
        """
        Function called from ir.cron that check all active sequence
        date_end and set state = expired if necessary
        """
        # Use DR local time
        l10n_do_date = get_l10n_do_datetime().date()
        fiscal_sequence_ids = self.search([('state', '=', 'active')])

        for seq in fiscal_sequence_ids.filtered(
                lambda s: l10n_do_date >= s.date_end):
            seq.state = 'expired'

    def get_fiscal_number(self):
        if self.sequence_remaining > 0:
            sequence_next = self.sequence_id._next()

            # After consume a sequence, evaluate if sequence
            # is depleted and set state to depleted
            if (self.sequence_remaining - 1) < 1:
                self.state = 'depleted'

            return "%s%s" % (
                self.fiscal_type_id.prefix,
                str(sequence_next).zfill(self.sequence_id.padding))
        else:
            raise ValidationError(
                _('No Fiscal Sequence available for this type of document.'))


class AccountFiscalType(models.Model):
    _name = 'account.fiscal.type'
    _description = "Account Fiscal Type"
    _order = 'sequence'

    name = fields.Char(
        required=True,
        copy=False,
    )
    sequence = fields.Integer()
    prefix = fields.Char(
        copy=False,
    )
    type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('special', 'Special')
    ],
        required=True,
    )
    fiscal_position_id = fields.Many2one(
        "account.fiscal.position",
        string="Fiscal Position",
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Journal"
    )
    internal_generate = fields.Boolean(
        default=True,
    )
    required_document = fields.Boolean(
        string="Required document",
    )

