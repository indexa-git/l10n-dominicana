# © 2018 Manuel Marquez <buzondemam@gmail.com>

from odoo import models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("purchase_vendor_bill_id", "purchase_id", "company_id", "journal_id")
    def _onchange_purchase_auto_complete(self):
        # Compute ref.
        super()._onchange_purchase_auto_complete()

        if (
            self.company_id.country_id.code == "DO"
            and self.l10n_latam_use_documents
        ):
            refs = set(self.line_ids.mapped("purchase_line_id.order_id.partner_ref"))
            refs = [ref for ref in refs if ref]
            self.narration = ",".join(refs)
            self.ref = False
