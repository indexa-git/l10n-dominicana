from odoo import models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        "posted_before",
        "state",
        "journal_id",
        "date",
        "move_type",
        "payment_id",
    )
    def _compute_name(self):
        # Keep the standard (and l10n_latam_invoice_document) name computation for
        # every company; only Dominican fiscal documents get the extra logic below.
        super()._compute_name()

        # ``l10n_latam_invoice_document._compute_name`` blanks the ``name`` of
        # manually numbered purchase documents (vendor bills/refunds). In the
        # Dominican localization those documents must keep an internal move
        # sequence (e.g. ``COMP/2026/0001``); the fiscal NCF is stored
        # separately in ``l10n_do_fiscal_number``. Re-assign the internal
        # sequence for any posted DO fiscal document left without a name.
        for move in self.filtered(
            lambda x: x.country_code == "DO"
            and x.l10n_latam_use_documents
            and x.state == "posted"
            and x.date
            and (not x.name or x.name == "/")
        ):
            move._set_next_sequence()

        # Assign the Dominican fiscal number (NCF) on internally generated
        # fiscal documents once posted.
        for move in self.filtered(
            lambda x: x.country_code == "DO"
            and x.l10n_latam_document_type_id
            and not x.l10n_latam_manual_document_number
            and not x.l10n_do_enable_first_sequence
            and x.state == "posted"
            and not x.l10n_do_fiscal_number
        ):
            move.with_context(is_l10n_do_seq=True)._set_next_sequence()
