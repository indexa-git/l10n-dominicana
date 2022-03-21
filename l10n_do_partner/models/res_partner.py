from odoo import models, api, _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    @api.constrains('vat', 'company_id')
    def _check_unique_contact_nif(self):
        for rec in self:
            if rec.same_vat_partner_id:
                raise ValidationError(
                    _("A partner named {} with same Tax ID already exists.").format(
                        rec.same_vat_partner_id.name
                    )
                )
