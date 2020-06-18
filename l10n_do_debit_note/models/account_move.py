from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def init(self):  # DO NOT FORWARD PORT
        """
        Fill debit_origin_id field of all existing debit notes
        """

        debit_notes = self.search([
            ("is_debit_note", "=", True),
            ("debit_origin_id", "=", False),
        ])

        for dn in debit_notes:
            debit_origin_id = self.search(
                [("ref", "=", dn.l10n_do_origin_ncf)], limit=1
            )
            dn.debit_origin_id = debit_origin_id
