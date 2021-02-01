from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_view_invoice(self):

        res = super(PurchaseOrder, self).action_view_invoice()

        ctx = res["context"]

        is_l10n_do = (
            self.env["res.company"].browse(ctx["default_company_id"]).country_id.code
            == "DO"
            and self.env["account.move"]
            .with_context(
                default_type=ctx["default_type"],
                default_company_id=ctx["default_company_id"],
            )
            ._get_default_journal()
            .l10n_latam_use_documents
        )

        if is_l10n_do:
            del ctx["default_ref"]

        return res
