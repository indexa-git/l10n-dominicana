from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_do_fiscal_journal = fields.Boolean(string="Fiscal Journal")

    payment_form = fields.Selection(
        [
            ("cash", "Cash"),
            ("bank", "Check / Transfer"),
            ("card", "Credit Card"),
            ("credit", "Credit"),
            ("swap", "Swap"),
            ("bond", "Bonds or Gift Certificate"),
            ("others", "Other Sale Type"),
        ],
        string="Payment Form",
    )

    @api.constrains("l10n_do_fiscal_journal")
    def check_l10n_do_fiscal_journal(self):
        for journal in self:
            if journal.env["account.invoice"].search_count(
                [("journal_id", "=", journal.id), ("state", "!=", "draft")], limit=1
            ):
                raise ValidationError(
                    _(
                        'You can not modify the field "Fiscal Journal" if there are '
                        'validated invoices in this journal!'
                    )
                )
