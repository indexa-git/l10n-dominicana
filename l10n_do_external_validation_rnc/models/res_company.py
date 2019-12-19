from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    can_validate_rnc = fields.Boolean(
        string="Validate RNC/Cedula",
        default=True,
    )
