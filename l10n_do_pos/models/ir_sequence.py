from odoo import models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def get_l10n_do_fiscal_info(self):
        return {
            "ncf": self.next_by_id(),
            "expiration_date": self.expiration_date,
        }
