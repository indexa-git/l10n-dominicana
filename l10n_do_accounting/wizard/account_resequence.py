from odoo import models, api, _
from odoo.exceptions import UserError


class ReSequenceWizard(models.TransientModel):
    _inherit = "account.resequence.wizard"

    @api.model
    def default_get(self, fields_list):
        ctx = self.env.context
        if (
            "active_model" in ctx
            and ctx["active_model"] == "account.move"
            and "active_ids" in ctx
            and "skip_validation" not in ctx
        ):
            l10n_do_move_ids = (
                self.env["account.move"]
                .browse(ctx["active_ids"])
                .filtered(
                    lambda inv: inv.l10n_latam_use_documents
                    and inv.country_code == "DO"
                )
            )

            if l10n_do_move_ids:
                raise UserError(_("Fiscal invoices resequence is not allowed."))

        return super(ReSequenceWizard, self).default_get(fields_list)
