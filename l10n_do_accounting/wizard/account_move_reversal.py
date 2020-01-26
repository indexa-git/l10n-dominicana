
from odoo import models, api, fields


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    l10n_latam_country_code = fields.Char(
        related='move_id.company_id.country_id.code',
        help='Technical field used to hide/show fields regarding the localization')

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveReversal, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', False)
        if active_ids and len(active_ids) == 1:
            move_id = self.env['account.move'].browse(active_ids)
            res['move_id'] = move_id.id if move_id.company_id.country_id.code == 'DO' \
                else False

        return res
