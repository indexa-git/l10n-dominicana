
from odoo import models, api, fields


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    @api.model
    def _get_refund_type_selection(self):
        selection = [
            ("full_refund", "Full Refund"),
            ("percentage", "Percentage"),
            ("fixed_amount", "Amount"),
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

        name = "debit" if self._context.get("debit_note") else "Refund"

        return [
            ("draft_refund", "Partial %s" % name),
            ("apply_refund", "Full %s" % name),
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
        help='Technical field used to hide/show fields regarding the localization')
    refund_type = fields.Selection(
        selection=_get_refund_type_selection,
        default=_get_default_refund_type,
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
            res['move_id'] = move_id.id if move_id.company_id.country_id.code == 'DO' \
                else False

        return res

    @api.onchange("refund_type")
    def onchange_refund_type(self):
        if self.refund_type != "full_refund":
            self.refund_method = "refund"

    @api.onchange("refund_action")
    def onchange_refund_action(self):
        if self.refund_action == "apply_refund":
            self.refund_method = "cancel"

    def reverse_moves(self):

        return super(AccountMoveReversal, self.with_context(
            refund_type=self.refund_type,
            percentage=self.percentage,
            amount=self.amount,
            account_id=self.account_id.id,
            reason=self.reason,
        )).reverse_moves()
