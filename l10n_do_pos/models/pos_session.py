from odoo import fields, models, api


class PosSession(models.Model):
    _inherit = "pos.session"

    def action_pos_session_close(self):
        self.config_id._check_company_journal()
        return super(PosSession, self).action_pos_session_close()
