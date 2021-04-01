from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError


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

    l10n_latam_country_code = fields.Char(
        default=lambda self: self.env.company.country_code,
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
        help="Debit Note based on origin invoice percentage",
        string="Percentage",
    )
    l10n_do_amount = fields.Float(
        help="Debit Note based fixed amount",
        string="Amount",
    )
    l10n_do_account_id = fields.Many2one(
        "account.account",
        string="Account",
        domain=[("deprecated", "=", False)],
    )
    l10n_latam_document_number = fields.Char(
        string="Document Number",
    )
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

    @api.model
    def default_get(self, fields):

        res = super(AccountDebitNote, self).default_get(fields)

        move_ids = (
            self.env["account.move"].browse(self.env.context["active_ids"])
            if self.env.context.get("active_model") == "account.move"
            else self.env["account.move"]
        )

        if not move_ids:
            raise UserError(_("No invoice found for this operation"))

        move_ids_use_document = move_ids.filtered(
            lambda move: move.l10n_latam_use_documents
            and move.company_id.country_code == "DO"
        )
        if move_ids_use_document and not self.env.user.has_group(
            "l10n_do_accounting.group_l10n_do_debit_note"
        ):
            raise AccessError(_("You are not allowed to issue Debit Notes"))

        # Setting default account
        journal = move_ids[0].journal_id
        res["l10n_do_account_id"] = journal.default_account_id.id

        # Do not allow Debit Notes if Comprobante de Compra or Gastos Menores
        if move_ids[0].l10n_latam_document_type_id.l10n_do_ncf_type in (
            "informal",
            "minor",
            "e-informal",
            "e-minor",
        ):
            raise UserError(
                _("You cannot issue Credit/Debit Notes for %s document type")
                % move_ids_use_document.l10n_latam_document_type_id.name
            )

        if len(move_ids_use_document) > 1:
            raise UserError(
                _("You cannot create Debit Notes from multiple documents at a time.")
            )
        else:
            res["is_ecf_invoice"] = move_ids_use_document[0].is_ecf_invoice

        return res

    def _get_line_tax(self):

        if self.move_type == "out_invoice":
            return (
                self.move_ids[0].company_id.account_sale_tax_id
                or self.env.ref("l10n_do.1_tax_18_sale")
                if (self.date - self.move_ids[0].invoice_date).days <= 30
                and self.move_ids[0].partner_id.l10n_do_dgii_tax_payer_type != "special"
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
                    l10n_do_ecf_modification_code=self.l10n_do_ecf_modification_code,
                    l10n_latam_document_number=self.l10n_latam_document_number,
                    l10n_do_origin_ncf=move.l10n_latam_document_number,
                    l10n_do_expense_type=move.l10n_do_expense_type,
                    l10n_do_income_type=move.l10n_do_income_type,
                    invoice_origin=move.name,
                    line_ids=[],
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
