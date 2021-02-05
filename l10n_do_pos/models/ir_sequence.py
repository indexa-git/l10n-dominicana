from odoo import api, fields, models


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def get_expiration_date_and_next_by_id(self):
        return{
            'ncf': self.next_by_id(),
            'expiration_date': self.expiration_date,
        }
