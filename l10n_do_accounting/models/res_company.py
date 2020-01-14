from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_do_country_code = fields.Char(related='country_id.code', string='Country Code')
    l10n_do_dgii_start_date = fields.Date('Activities Start Date')

    l10n_do_default_client = fields.Selection(
        selection=[('non_payer', 'Final Consumer'), ('taxpayer', 'Fiscal Consumer'), ],
        default=lambda self: self._context.get('l10n_do_default_client', 'non_payer'),
        string='Default Customer',
    )

    def _localization_use_documents(self):
        """ Dominican localization uses documents """
        self.ensure_one()
        return (
            True
            if self.country_id == self.env.ref('base.do')
            else super()._localization_use_documents()
        )
