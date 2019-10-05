# © 2019 José López <jlopez@indexa.do>


from odoo import models, fields, api


class AccountFiscalSequence(models.Model):
    _name = 'account.fiscal.sequence'
    _description = "Account Fiscal Sequence"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Authorization number",
        required=True,
    )
    expiration_date = fields.Date(
        required=True,
    )
    fiscal_type_id = fields.Many2one(
        'account.fiscal.type',
        required=True,
    )
    type = fields.Selection(
        related='fiscal_type_id.type',
        store=True,
    )
    sequence_start = fields.Integer(
        required=True,
    )
    sequence_end = fields.Integer(
        required=True,
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
        # TODO: implement compute method
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('active', 'Active'),
        ('depleted', 'Depleted'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], default='draft',
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
    )

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
        pass

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        pass


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

