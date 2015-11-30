# -*- coding: utf-8 -*-


from openerp import models, fields, api, exceptions


class ShopJournalConfig(models.Model):
    _name = "shop.ncf.config"


    name = fields.Char("Nombre", size=40, required=True)
    sale_journal_id = fields.Many2one("account.journal", "Diario de ventas", required=False, domain="[('type','=','sale')]")
    user_ids = fields.Many2many("res.users", string="Usuarios que pueden usar esta sucursal")


    _sql_constraints = [
        ('shop_ncf_config_name_uniq', 'unique(name)', 'El nombre de la sucursal debe de ser unico!'),
    ]

    def get_user_shop_domain(self):
        user_shops = self.search([('user_ids','=',self._uid)])
        return [('id','=',[r.id for r in user_shops])]

    @api.v8
    @api.multi
    def get_default_shop(self):
        try:
            user_shops = self.search([('user_ids','=',self._uid)])
            if user_shops:
                if len(user_shops) > 1:
                    return user_shops[0].id
                else:
                    return user_shops.id
            else:
                raise exceptions.Warning(u"Se debe realizar la configuración de los comprobantes fiscales antes de realizar una factura!")
        except:
            return False