from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = "pos.config"

    pos_default_partner_id = fields.Many2one("res.partner",
                                             help="Este cliente se usará por defecto como cliente de consumo para las facturas de consumo o final en el POS")
    print_pdf = fields.Selection([(False, 'No (Default)'), (True, 'Si')], default=False)

    @api.onchange("iface_invoicing")
    def onchange_iface_invoicing(self):
        default_partner = self.env.ref("ncf_pos.default_partner_on_pos", raise_if_not_found=False)
        if self.iface_invoicing and default_partner:
            self.pos_default_partner_id = default_partner.id
        else:
            self.pos_default_partner_id = False
