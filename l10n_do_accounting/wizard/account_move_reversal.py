from odoo import models, api, fields, _


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    @api.model
    def _get_refund_type_selection(self):
        selection = [
            ("full_refund", _("Full Refund")),
            ("percentage", _("Percentage")),
            ("fixed_amount", _("Amount")),
        ]
        if self._context.get("debit_note"):
            selection.pop(0)

        return selection

    @api.model
    def _get_default_refund_type(self):
        if self._context.get("debit_note"):
            return "percentage"
        return "full_refund"

    @api.model
    def _get_refund_action_selection(self):

        name = _("debit") if self._context.get("debit_note") else _("Refund")

        return [
            ("draft_refund", _("Partial %s") % name),
            ("apply_refund", _("Full %s") % name),
        ]

    @api.model
    def _default_account(self):
        journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", self.env.user.company_id.id)],
            limit=1,
        )
        if self._context.get("type") in ("out_invoice", "in_refund"):
            return journal.default_credit_account_id.id
        return journal.default_debit_account_id.id

    l10n_latam_country_code = fields.Char(
        related='move_id.company_id.country_id.code',
        help='Technical field used to hide/show fields regarding the localization',
    )
    refund_type = fields.Selection(
        selection=_get_refund_type_selection, default=_get_default_refund_type,
    )
    refund_action = fields.Selection(
        selection=_get_refund_action_selection,
        default="draft_refund",
        string="Refund Action",
    )
    percentage = fields.Float()
    amount = fields.Float()
    account_id = fields.Many2one(
        "account.account",
        string="Account",
        domain=[("deprecated", "=", False)],
        default=_default_account,
    )

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveReversal, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', False)
        if active_ids and len(active_ids) == 1:
            move_id = self.env['account.move'].browse(active_ids)
            res['move_id'] = (
                move_id.id if move_id.company_id.country_id.code == 'DO' else False
            )

        return res

    @api.onchange("refund_type")
    def onchange_refund_type(self):
        if self.refund_type != "full_refund":
            self.refund_method = "refund"

    @api.onchange("refund_action")
    def onchange_refund_action(self):
        if self.refund_action == "apply_refund":
            self.refund_method = "cancel"
        else:
            self.refund_method = "refund"

    def reverse_moves(self):

        return super(
            AccountMoveReversal,
            self.with_context(
                refund_type=self.refund_type,
                percentage=self.percentage,
                amount=self.amount,
                account_id=self.account_id.id,
                reason=self.reason,
            ),
        ).reverse_moves()

    def generate_debit_note_move(self):

        moves = (
            self.env['account.move'].browse(self.env.context['active_ids'])
            if self.env.context.get('active_model') == 'account.move'
            else self.move_id
        )
        invoice_type = self.env.context.get('debit_note')

        # Create default values.
        default_values_list = []
        for move in moves:
            price_unit = (
                self.amount
                if self.refund_type == "fixed_amount"
                else move.amount_untaxed * (self.percentage / 100)
            )
            default_values_list.append(
                {
                    'date': self.date or move.date,
                    'invoice_date': move.is_invoice(include_receipts=True)
                    and (self.date or move.date)
                    or False,
                    'journal_id': self.journal_id
                    and self.journal_id.id
                    or move.journal_id.id,
                    'invoice_payment_term_id': None,
                    'auto_post': True
                    if self.date > fields.Date.context_today(self)
                    else False,
                    'invoice_line_ids': [
                        (
                            0,
                            0,
                            {
                                'name': self.reason,
                                'price_unit': price_unit,
                                'account_id': self.account_id.id,
                            },
                        )
                    ],
                    'is_debit_note': True,
                    'type': invoice_type,
                    'partner_id': move.partner_id.commercial_partner_id.id,
                    'l10n_do_origin_ncf': move.l10n_latam_document_number,
                    'l10n_do_income_type': move.l10n_do_income_type,
                    'l10n_do_expense_type': move.l10n_do_expense_type,
                    'l10n_latam_document_number': self.l10n_latam_document_number,
                }
            )
        debit_moves = (
            self.env['account.move']
            .with_context(internal_type='debit_note')
            .create(default_values_list)
        )
        if self.refund_action == 'apply_refund':
            debit_moves.post()
        action = {
            'name': _('Debit Notes'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
        }
        if len(debit_moves) == 1:
            action.update(
                {'view_mode': 'form', 'res_id': debit_moves.id, }
            )
        else:
            action.update(
                {
                    'view_mode': 'tree,form',
                    'domain': [
                        ('id', 'in', debit_moves.ids),
                        ('type', '=', invoice_type),
                        ('is_debit_note', '=', True),
                    ],
                }
            )
        return action
