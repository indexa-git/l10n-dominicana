from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_can_validate_rnc = fields.Boolean(
        string="Validate RNC/Cedula",
        related="company_id.can_validate_rnc",
        readonly=False,
    )
