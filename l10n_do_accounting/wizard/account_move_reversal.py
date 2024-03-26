from odoo import models, api, fields, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    @api.model
    def _get_l10n_do_refund_type_selection(self):
        selection = [
            ("full_refund", _("Full Refund")),
            ("percentage", _("Percentage")),
            ("fixed_amount", _("Amount")),
        ]

        return selection

    @api.model
    def _get_default_l10n_do_refund_type(self):
        return "full_refund"

    @api.model
    def _get_refund_action_selection(self):
        return [
            ("draft_refund", _("Partial Refund")),
            ("apply_refund", _("Full Refund")),
        ]

    @api.model
    def _default_account(self):
        move_type = self._context.get("move_type")
        journal = (
            self.env["account.move"]
            .with_context(
                default_type=move_type, default_company_id=self.env.company.id
            )
            ._get_default_journal()
        )
        if move_type in ("out_invoice", "in_refund"):
            return journal.default_credit_account_id.id
        return journal.default_debit_account_id.id

    country_code = fields.Char(
        related="company_id.country_code",
        help="Technical field used to hide/show fields regarding the localization",
    )
    l10n_do_refund_type = fields.Selection(
        selection=_get_l10n_do_refund_type_selection,
        default=_get_default_l10n_do_refund_type,
    )
    l10n_do_percentage = fields.Float("Percentage")
    l10n_do_amount = fields.Float("Amount")
    l10n_do_ecf_modification_code = fields.Selection(
        selection=lambda self: self.env[
            "account.move"
        ]._get_l10n_do_ecf_modification_code(),
        string="e-CF Modification Code",
        copy=False,
    )
    is_ecf_invoice = fields.Boolean(
        string="Is Electronic Invoice",
    )

    @api.depends(
        "l10n_latam_document_type_id", "country_code", "l10n_latam_use_documents"
    )
    def _compute_l10n_latam_manual_document_number(self):
        self.l10n_latam_manual_document_number = False
        l10n_do_recs = self.filtered(
            lambda r: r.move_ids
            and r.l10n_latam_use_documents
            and r.country_code == "DO"
        )
        for rec in l10n_do_recs:
            move = rec.move_ids[0]
            rec.l10n_latam_manual_document_number = (
                move.l10n_latam_manual_document_number
            )

        super(
            AccountMoveReversal, self - l10n_do_recs
        )._compute_l10n_latam_manual_document_number()

    # @api.onchange("l10n_do_refund_type")
    # def onchange_l10n_do_refund_type(self):
    #     if self.l10n_do_refund_type != "full_refund":
    #         self.refund_method = "refund"

    # @api.onchange("l10n_do_refund_action")
    # def onchange_refund_action(self):
    #     if self.l10n_do_refund_action == "apply_refund":
    #         self.refund_method = "cancel"
    #     else:
    #         self.refund_method = "refund"

    def _prepare_default_reversal(self, move):
        result = super(AccountMoveReversal, self)._prepare_default_reversal(move)

        if self.country_code == "DO":
            result.update(
                {
                    "l10n_do_ecf_modification_code": self.l10n_do_ecf_modification_code,
                    "l10n_latam_document_number": self.l10n_latam_document_number,
                    "l10n_do_origin_ncf": move.l10n_do_fiscal_number or move.ref,
                    "l10n_do_expense_type": move.l10n_do_expense_type,
                    "l10n_do_income_type": move.l10n_do_income_type,
                    "invoice_origin": move.name,
                }
            )

            if self.l10n_do_refund_type != "full_refund":
                result.update(
                    {
                        "l10n_latam_document_type_id": self.l10n_latam_document_type_id.id,
                        "line_ids": [(5, 0, 0)],
                    }
                )

                price_unit = (
                    self.l10n_do_amount
                    if self.l10n_do_refund_type == "fixed_amount"
                    else move.amount_untaxed * (self.l10n_do_percentage / 100)
                )
                result["invoice_line_ids"] = [
                    (
                        0,
                        0,
                        {
                            "name": self.reason or _("Credit"),
                            "price_unit": price_unit,
                            "quantity": 1,
                        },
                    )
                ]

        return result

    @api.depends("move_ids", "journal_id")
    def _compute_document_type(self):
        self.l10n_latam_available_document_type_ids = False
        self.l10n_latam_document_type_id = False
        self.l10n_latam_use_documents = False
        do_wizard = self.filtered(
            lambda w: w.journal_id
            and w.journal_id.l10n_latam_use_documents
            and w.country_code == "DO"
        )
        for record in do_wizard:
            if len(record.move_ids) > 1:
                move_ids_use_document = record.move_ids._origin.filtered(
                    lambda move: move.l10n_latam_use_documents
                )
                if move_ids_use_document:
                    raise UserError(
                        _(
                            "You can only reverse documents with legal invoicing documents from Latin America "
                            "one at a time.\nProblematic documents: %s"
                        )
                        % ", ".join(move_ids_use_document.mapped("name"))
                    )
            else:
                record.write(
                    {
                        "l10n_latam_use_documents": record.journal_id.l10n_latam_use_documents,
                        "is_ecf_invoice": record.company_id.l10n_do_ecf_issuer,
                    }
                )

            if record.l10n_latam_use_documents:
                refund = record.env["account.move"].new(
                    {
                        "move_type": record._reverse_type_map(
                            record.move_ids.move_type
                        ),
                        "journal_id": record.journal_id.id,
                        "partner_id": record.move_ids.partner_id.id,
                        "company_id": record.move_ids.company_id.id,
                    }
                )
                record.l10n_latam_document_type_id = refund.l10n_latam_document_type_id
                record.l10n_latam_available_document_type_ids = (
                    refund.l10n_latam_available_document_type_ids
                )
        super(AccountMoveReversal, self - do_wizard)._compute_document_type()
