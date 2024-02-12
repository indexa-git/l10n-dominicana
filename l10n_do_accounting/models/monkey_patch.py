from odoo import models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        "posted_before", "state", "journal_id", "date", "move_type", "payment_id"
    )
    def _compute_name(self):
        super(AccountMove, self)._compute_name()

        for move in self.filtered(
            lambda x: x.country_code == "DO"
            and x.l10n_latam_document_type_id
            and not x.l10n_latam_manual_document_number
            and not x.l10n_do_enable_first_sequence
        ):
            move.with_context(is_l10n_do_seq=True)._set_next_sequence()
