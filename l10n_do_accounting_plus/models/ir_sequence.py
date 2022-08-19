from odoo import models, fields


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    expiration_date = fields.Date(
        string="NCF Expiration date",
        default=fields.Date.end_of(
            fields.Date.today().replace(year=fields.Date.today().year + 1), "year"
        ),
    )
    # l10n_latam_journal_id = fields.Many2one('account.journal', 'Journal')
    # TODO: Note for anyone from the future: use l10n_do prefix on v14, for God sake
