from odoo import models, api, fields, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    @api.model
    def _get_refund_type_selection(self):
        selection = [
            ("full_refund", _("Full Refund")),
            ("percentage", _("Percentage")),
            ("fixed_amount", _("Amount")),
        ]

        return selection

    @api.model
    def _get_default_refund_type(self):
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
    l10n_do_enable_first_sequence = fields.Boolean(
        string="Enable first fiscal sequence",
        compute="_compute_l10n_do_enable_first_sequence",
        help="Technical field that compute if internal generated fiscal sequence "
        "is enabled to be set manually.",
    )

    @api.depends(
        "journal_id.l10n_latam_use_documents",
        "l10n_latam_manual_document_number",
        "l10n_latam_document_type_id",
        "company_id",
    )
    def _compute_l10n_do_enable_first_sequence(self):
        """
        Enable first fiscal sequence manual input on internal generated documents
        if no invoice of same document type was posted before
        """
        l10n_do_internal_invoices = self.filtered(
            lambda wizard: wizard.l10n_latam_use_documents
            and wizard.l10n_latam_document_type_id
            and wizard.country_code == "DO"
            and not wizard.l10n_latam_manual_document_number
        )
        for invoice in l10n_do_internal_invoices:
            invoice.l10n_do_enable_first_sequence = (
                not bool(
                    self.search_count(
                        [
                            ("company_id", "=", invoice.company_id.id),
                            ("move_type", "=", invoice.move_type),
                            (
                                "l10n_latam_document_type_id",
                                "=",
                                invoice.l10n_latam_document_type_id.id,
                            ),
                            ("posted_before", "=", True),
                            ("id", "!=", invoice.id or invoice._origin.id),
                        ],
                    )
                )
                or invoice.l10n_do_show_expiration_date_msg
            )

        (self - l10n_do_internal_invoices).l10n_do_enable_first_sequence = False

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

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveReversal, self).default_get(fields)
        move_ids = (
            self.env["account.move"].browse(self.env.context["active_ids"])
            if self.env.context.get("active_model") == "account.move"
            else self.env["account.move"]
        )
        move_ids_use_document = move_ids.filtered(
            lambda move: move.l10n_latam_use_documents
            and move.company_id.country_code == "DO"
        )

        if len(move_ids_use_document) > 1:
            raise UserError(
                _(
                    "You cannot create Credit Notes from multiple "
                    "documents at a time."
                )
            )
        if move_ids_use_document:
            res["is_ecf_invoice"] = move_ids_use_document[
                0
            ].company_id.l10n_do_ecf_issuer

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
                reason=self.reason,
                l10n_do_ecf_modification_code=self.l10n_do_ecf_modification_code,
            ),
        ).reverse_moves()

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
                record.l10n_latam_use_documents = (
                    record.journal_id.l10n_latam_use_documents
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

    @api.depends("l10n_latam_document_type_id")
    def _compute_l10n_latam_manual_document_number(self):
        self.l10n_latam_manual_document_number = False
        do_wizard = self.filtered(
            lambda w: w.journal_id
            and w.journal_id.l10n_latam_use_documents
            and w.country_code == "DO"
            and w.move_ids
        )
        for rec in do_wizard:
            if rec.journal_id and rec.journal_id.l10n_latam_use_documents:
                rec.l10n_latam_manual_document_number = self.env[
                    "account.move"
                ]._is_manual_document_number(rec.journal_id)
        super(
            AccountMoveReversal, self - do_wizard
        )._compute_l10n_latam_manual_document_number()
