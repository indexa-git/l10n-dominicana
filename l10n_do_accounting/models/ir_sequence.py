import datetime

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class IrSequence(models.Model):

    _inherit = 'ir.sequence'

    l10n_do_sequence = fields.Selection(
        selection='_get_l10n_do_sequences', string='sequence',
    )

    def _get_l10n_do_sequences(self):
        """ Return the list of values of the selection field. """
        return self.env['l10n_latam.document.type']._get_l10n_do_sequences()

    l10n_do_authorization_number = fields.Char(
        string="Authorization number",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )
    l10n_do_expiration_date = fields.Date(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
        default=datetime.strptime(
            str(int(str(fields.Date.today())[0:4]) + 1) + '-12-31', '%Y-%m-%d'
        ).date(),
    )
    # l10n_latam_document_type_id = fields.Many2one(
    #     'account.document.type',
    #     required=True,
    #     readonly=True,
    #     states={'draft': [('readonly', False)]},
    #     track_visibility='onchange',
    # )
    # l10n_do_type = fields.Selection(
    #     related='l10n_latam_document_type_id.l10n_do_type', store=True,
    # )
    l10n_do_sequence_start = fields.Integer(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
        default=1,
        copy=False,
    )
    l10n_do_sequence_end = fields.Integer(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
        default=1,
        copy=False,
    )
    l10n_do_sequence_remaining = fields.Integer(
        string='Remaining', compute='_compute_sequence_remaining',
    )

    l10n_do_warning_gap = fields.Integer(compute='_compute_warning_gap',)
    l10n_do_remaining_percentage = fields.Float(
        default=35,
        required=True,
        help="Fiscal Sequence remaining percentage to reach to start "
        "warning notifications.",
    )

    l10n_do_next_fiscal_number = fields.Char(compute='_compute_next_fiscal_number',)
    l10n_do_sequence_state = fields.Selection(
        [
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
    l10n_do_can_be_queued = fields.Boolean(compute='_compute_can_be_queued',)
    company_id = fields.Many2one(
        states={'draft': [('readonly', False)]}, track_visibility='onchange',
    )

    @api.depends('l10n_do_sequence_state')
    def _compute_can_be_queued(self):
        for rec in self:
            if rec.l10n_do_sequence_state == 'draft':
                rec.l10n_do_can_be_queued = bool(
                    2
                    > self.search_count(
                        [
                            ('l10n_do_sequence_state', 'in', ('active', 'queue')),
                            (
                                'l10n_latam_document_type_id',
                                '=',
                                rec.l10n_latam_document_type_id.id,
                            ),
                            ('company_id', '=', rec.company_id.id),
                        ]
                    )
                    > 0
                )
            else:
                rec.l10n_do_can_be_queued = False

    @api.depends('l10n_do_remaining_percentage')
    def _compute_warning_gap(self):
        for rec in self:
            rec.l10n_do_warning_gap = (
                rec.l10n_do_sequence_end - (rec.l10n_do_sequence_start - 1)
            ) * (rec.l10n_do_remaining_percentage / 100)

    @api.depends('l10n_do_sequence_end', 'l10n_do_sequence_id.number_next')
    def _compute_sequence_remaining(self):
        for rec in self:
            if rec.l10n_do_sequence_id:
                # Sequence remaining
                rec.l10n_do_sequence_remaining = (
                    rec.l10n_do_sequence_end
                    - rec.l10n_do_sequence_id.number_next_actual
                    + 1
                )

    @api.depends(
        'l10n_latam_document_type_id.doc_code_prefix',
        'l10n_do_sequence_id.padding',
        'l10n_do_sequence_id.number_next_actual',
    )
    def _compute_next_fiscal_number(self):
        for seq in self:
            seq.l10n_do_next_fiscal_number = "%s%s" % (
                seq.l10n_latam_document_type_id.doc_code_prefix,
                str(seq.l10n_do_sequence_id.number_next_actual).zfill(
                    seq.l10n_do_sequence_id.padding
                ),
            )

    @api.onchange('l10n_latam_document_type_id')
    def _onchange_fiscal_type_id(self):
        """
        Compute draft Fiscal Sequence default l10n_do_sequence_start
        """
        if self.l10n_latam_document_type_id and self.l10n_do_sequence_state == 'draft':
            # Last active or depleted Fiscal Sequence
            fs_id = self.search(
                [
                    (
                        'l10n_latam_document_type_id',
                        '=',
                        self.l10n_latam_document_type_id.id,
                    ),
                    ('l10n_do_sequence_state', 'in', ('depleted', 'active')),
                    ('company_id', '=', self.company_id.id),
                ],
                order='l10n_do_sequence_end desc',
                limit=1,
            )
            self.l10n_do_sequence_start = fs_id.l10n_do_sequence_end + 1 if fs_id else 1

    @api.constrains('l10n_latam_document_type_id', 'l10n_do_sequence_state')
    def _validate_unique_active_type(self):
        """
        Validate an active sequence type uniqueness
        """
        domain = [
            ('l10n_do_sequence_state', '=', 'active'),
            ('l10n_latam_document_type_id', '=', self.l10n_latam_document_type_id.id),
            ('company_id', '=', self.company_id.id),
        ]
        if self.search_count(domain) > 1:
            raise ValidationError(_("Another sequence is active for this type."))

    @api.constrains(
        'l10n_do_sequence_start',
        'l10n_do_sequence_end',
        'l10n_do_sequence_state',
        'l10n_latam_document_type_id',
        'company_id',
    )
    def _validate_sequence_range(self):
        for rec in self.filtered(lambda s: s.l10n_do_sequence_state != 'cancelled'):
            if any(
                [
                    True
                    for value in [rec.l10n_do_sequence_start, rec.l10n_do_sequence_end]
                    if value <= 0
                ]
            ):
                raise ValidationError(_('Sequence values must be greater than zero.'))
            if rec.l10n_do_sequence_start >= rec.l10n_do_sequence_end:
                raise ValidationError(
                    _('End sequence must be greater than start sequence.')
                )
            domain = [
                ('l10n_do_sequence_start', '>=', rec.l10n_do_sequence_start),
                ('l10n_do_sequence_end', '<=', rec.l10n_do_sequence_end),
                (
                    'l10n_latam_document_type_id',
                    '=',
                    rec.l10n_latam_document_type_id.id,
                ),
                ('l10n_do_sequence_state', 'in', ('active', 'queue')),
                ('company_id', '=', rec.company_id.id),
            ]
            if self.search_count(domain) > 1:
                raise ValidationError(
                    _("You cannot use another Fiscal Sequence range.")
                )

    def unlink(self):
        for rec in self:
            if rec.l10n_do_sequence_id:
                rec.l10n_do_sequence_id.sudo().unlink()
        return super().unlink()

    def name_get(self):
        result = []
        for sequence in self:
            result.append(
                (
                    sequence.id,
                    "%s - %s"
                    % (
                        sequence.l10n_do_authorization_number,
                        sequence.l10n_latam_document_type_id.l10n_do_authorization_number,
                    ),
                )
            )
        return result

    def action_view_sequence(self):
        self.ensure_one()
        l10n_do_sequence_id = self.l10n_do_sequence_id
        action = self.env.ref('base.ir_sequence_form').read()[0]
        if l10n_do_sequence_id:
            action['views'] = [(self.env.ref('base.sequence_view').id, 'form')]
            action['res_id'] = l10n_do_sequence_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_confirm(self):
        self.ensure_one()
        msg = _(
            'Are you sure want to confirm this Fiscal Sequence? '
            'Once you confirm this Fiscal Sequence cannot be edited.'
        )
        action = self.env.ref(
            'l10n_do_accounting.account_fiscal_sequence_validate_wizard_action'
        ).read()[0]
        action['context'] = {
            'default_name': msg,
            'default_l10n_latam_sequence_id': self.id,
            'action': 'confirm',
        }
        return action

    def _action_confirm(self):
        for rec in self:

            # Use DR local time
            l10n_do_date = fields.Date.today()

            if l10n_do_date >= rec.l10n_do_expiration_date:
                rec.l10n_do_sequence_state = 'expired'
            else:
                # Creates a new sequence of this Fiscal Sequence
                l10n_do_sequence_id = self.env['ir.sequence'].create(
                    {
                        'l10n_do_authorization_number': _('%s %s Sequence')
                        % (
                            rec.l10n_latam_document_type_id.l10n_do_authorization_number,
                            rec.l10n_do_authorization_number[-9:],
                        ),
                        'implementation': 'standard',
                        'padding': rec.l10n_latam_document_type_id.padding,
                        'number_increment': 1,
                        'number_next_actual': rec.l10n_do_sequence_start,
                        'number_next': rec.l10n_do_sequence_start,
                        'use_date_range': False,
                        'company_id': rec.company_id.id,
                    }
                )
                rec.write(
                    {
                        'l10n_do_sequence_state': 'active',
                        'l10n_do_sequence_id': l10n_do_sequence_id.id,
                    }
                )

    def action_cancel(self):
        self.ensure_one()
        msg = _(
            'Are you sure want to cancel this Fiscal Sequence? '
            'Once you cancel this Fiscal Sequence cannot be used.'
        )
        action = self.env.ref(
            'l10n_do_accounting.account_fiscal_sequence_validate_wizard_action'
        ).read()[0]
        action['context'] = {
            'default_name': msg,
            'default_l10n_latam_sequence_id': self.id,
            'action': 'cancel',
        }
        return action

    def _action_cancel(self):
        for rec in self:
            rec.l10n_do_sequence_state = 'cancelled'
            if rec.l10n_do_sequence_id:
                # *-*-*-*-*- Remove this comment *-*-*-*-*-*
                # Preserve internal sequence just for audit purpose.
                rec.l10n_do_sequence_id.active = False

    def action_queue(self):
        for rec in self:
            rec.l10n_do_sequence_state = 'queue'

    def _expire_sequences(self):
        """
        Function called from ir.cron that check all active sequence
        l10n_do_expiration_date and set l10n_do_sequence_state = expired if necessary
        """
        # Use DR local time
        l10n_do_date = fields.Date.today()
        l10n_latam_sequence_ids = self.search(
            [('l10n_do_sequence_state', '=', 'active')]
        )

        for seq in l10n_latam_sequence_ids.filtered(
            lambda s: l10n_do_date >= s.l10n_do_expiration_date
        ):
            seq.l10n_do_sequence_state = 'expired'

    def _get_queued_fiscal_sequence(self):
        l10n_latam_sequence_id = self.search(
            [
                ('l10n_do_sequence_state', '=', 'queue'),
                (
                    'l10n_latam_document_type_id',
                    '=',
                    self.l10n_latam_document_type_id.id,
                ),
                ('company_id', '=', self.company_id.id),
            ],
            order='l10n_do_sequence_start asc',
            limit=1,
        )
        return l10n_latam_sequence_id

    def get_fiscal_number(self):

        if not self.l10n_latam_document_type_id.l10n_latam_document_number:
            return False

        if self.l10n_do_sequence_remaining > 0:
            sequence_next = self.l10n_do_sequence_id._next()

            # After consume a sequence, evaluate if sequence
            # is depleted and set l10n_do_sequence_state to depleted
            if (self.l10n_do_sequence_remaining - 1) < 1:
                self.l10n_do_sequence_state = 'depleted'
                queue_sequence_id = self._get_queued_fiscal_sequence()
                if queue_sequence_id:
                    queue_sequence_id._action_confirm()

            return "%s%s" % (
                self.l10n_latam_document_type_id.doc_code_prefix,
                str(sequence_next).zfill(self.l10n_do_sequence_id.padding),
            )
        else:
            raise ValidationError(
                _('No Fiscal Sequence available for this type of document.')
            )
