# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    l10n_do_country_code = fields.Char(related='country_id.code',
                                       string='Country Code')
    l10n_do_dgii_start_date = fields.Date('Activities Start Date')

    l10n_do_default_consumer = fields.Selection(
        [('final', 'Final Consumer'),
         ('fiscal', 'Fiscal Consumer')],
        default=lambda self: self._context.get('l10n_do_default_consumer', 'final'))

    def _localization_use_documents(self):
        """ Dominican localization uses documents """
        self.ensure_one()
        return True if self.country_id == self.env.ref(
            'base.do') else super()._localization_use_documents()