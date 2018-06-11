# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class PosConfig(models.Model):
    _inherit = "pos.config"

    shop_id = fields.Many2one(comodel_name="shop.ncf.config", string="Sucursal")
    user_ids = fields.Many2many("res.users", string="Acceso para usuarios")
    default_partner_id = fields.Many2one("res.partner",
                                             help=u"Este cliente se usará por defecto como cliente de consumo para las facturas de consumo o final en el POS")
    print_pdf = fields.Boolean("Imprimir PDF", default=False)
    order_loading_options = fields.Selection(
        [("current_session", u"Cargar Órdenes de la Sesión actual"),
         ("n_days", u"Cargar Órdenes de los Últimos 'n' Días")],
        default='current_session', string="Opciones de Carga")
    number_of_days = fields.Integer(
        string=u'Cantidad de Días Anteriores', default=10)
    order_search_criteria = fields.Many2many('pos.search_criteria', string=u"Criterios de Búsqueda")
    ncf_control = fields.Boolean(related="invoice_journal_id.ncf_control")
    seller_and_cashier_ticket = fields.Boolean("Seller and Cashier on Ticket")

    @api.onchange("iface_invoicing")
    def onchange_iface_invoicing(self):
        default_partner = self.env.ref("ncf_pos.default_partner_on_pos", raise_if_not_found=False)
        if self.iface_invoicing and default_partner:
            self.default_partner_id = default_partner.id
        else:
            self.default_partner_id = False

    @api.constrains('number_of_days')
    def number_of_days_validation(self):
        if self.order_loading_options == 'n_days' and (not self.number_of_days or self.number_of_days < 0):
            raise exceptions.ValidationError(_(
                u"Favor proveer un valor válido para el campo 'Cantidad de Días Anteriores'!!!"))
