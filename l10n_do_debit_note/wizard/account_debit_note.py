from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountDebitNote(models.TransientModel):
    _inherit = "account.debit.note"

    @api.model
    def _get_l10n_do_debit_type_selection(self):
        selection = [
            ("percentage", _("Percentage")),
            ("fixed_amount", _("Amount")),
        ]
        return selection

    @api.model
    def _get_l10n_do_default_debit_type(self):
        return "percentage"

    @api.model
    def _get_l10n_do_debit_action_selection(self):

        return [
            ("draft_debit", _("Draft debit")),
            ("apply_debit", _("Apply debit")),
        ]

    @api.model
    def _default_l10n_do_account(self):
        journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", self.env.user.company_id.id)],
            limit=1,
        )
        if self._context.get("type") in ("out_invoice", "in_refund"):
            return journal.default_credit_account_id.id
        return journal.default_debit_account_id.id

    l10n_latam_country_code = fields.Char(
        default=lambda self: self.env.user.company_id.country_id.code,
        help="Technical field used to hide/show fields regarding the localization",
    )
    l10n_do_debit_type = fields.Selection(
        selection=_get_l10n_do_debit_type_selection,
        default=_get_l10n_do_default_debit_type,
        string="Debit Type",
    )
    l10n_do_debit_action = fields.Selection(
        selection=_get_l10n_do_debit_action_selection,
        default="draft_debit",
        string="Action",
    )
    l10n_do_percentage = fields.Float(
        help="Debit Note based on origin invoice percentage", string="Percentage",
    )
    l10n_do_amount = fields.Float(
        help="Debit Note based fixed amount", string="Amount",
    )
    l10n_do_account_id = fields.Many2one(
        "account.account",
        string="Account",
        domain=[("deprecated", "=", False)],
        default=_default_l10n_do_account,
    )
    l10n_latam_document_number = fields.Char(string="Document Number",)

    @api.model
    def default_get(self, fields):

        res = super(AccountDebitNote, self).default_get(fields)

        move_ids = (
            self.env["account.move"].browse(self.env.context["active_ids"])
            if self.env.context.get("active_model") == "account.move"
            else self.env["account.move"]
        )
        if len(move_ids) > 1:
            move_ids_use_document = move_ids.filtered(
                lambda move: move.l10n_latam_use_documents
                and move.company_id.country_id.code == "DO"
            )
            if move_ids_use_document:
                raise UserError(
                    _(
                        "You cannot created Debit Notes from multiple "
                        "documents at a time."
                    )
                )

        return res

    def _get_line_tax(self):

        if self.move_type == "out_invoice":
            return (
                self.move_ids[0].company_id.account_sale_tax_id
                or self.env.ref("l10n_do.1_tax_18_sale")
                if (self.date - self.move_ids[0].invoice_date).days <= 30
                else self.env.ref("l10n_do.1_tax_0_sale") or False
            )
        else:
            return self.move_ids[0].company_id.account_purchase_tax_id or self.env.ref(
                "l10n_do.1_tax_0_purch"
            )

    def _prepare_default_values(self, move):

        res = super(AccountDebitNote, self)._prepare_default_values(move)

        # Include additional info when l10n_do debit note
        if self.l10n_latam_country_code == "DO" and move.l10n_latam_use_documents:
            price_unit = (
                self.l10n_do_amount
                if self.l10n_do_debit_type == "fixed_amount"
                else move.amount_untaxed * (self.l10n_do_percentage / 100)
            )
            res.update(
                dict(
                    l10n_latam_document_number=self.l10n_latam_document_number,
                    l10n_do_origin_ncf=move.l10n_latam_document_number,
                    l10n_do_expense_type=move.l10n_do_expense_type,
                    l10n_do_income_type=move.l10n_do_income_type,
                    invoice_origin=move.name,
                    is_debit_note=True,
                    line_ids=False,
                    ref=move.name,
                    invoice_line_ids=[
                        (
                            0,
                            0,
                            {
                                "name": self.reason,
                                "price_unit": price_unit,
                                "account_id": self.l10n_do_account_id.id,
                                "tax_ids": [(6, 0, [self._get_line_tax().id])],
                            },
                        )
                    ],
                )
            )

        return res

    def create_debit(self):

        action = super(AccountDebitNote, self).create_debit()
        if (
            self.l10n_latam_country_code == "DO"
            and self.l10n_do_debit_action == "apply_debit"
        ):
            # Post Debit Note
            move_id = self.env["account.move"].browse(action.get("res_id", False))
            move_id.post()

        return action
