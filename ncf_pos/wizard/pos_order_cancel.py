# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions


class pos_cancel_order(models.TransientModel):
    _name = "pos.order.cancel"


    cancel_refund_info = fields.Many2many("order.info.tags")
    manager = fields.Char("Clave", required=True)

    @api.one
    def cancel(self):
        cancel = False

        if self.env.user.allow_cancel and self.env.user.pos_security_pin == self.manager:
            cancel = True

        if cancel:
            order = self.env["pos.order"].browse(self._context["active_id"])
            order.cancel_refund_info = [r.id for r in self.cancel_refund_info]
            order.action_cancel()
            return {'type': 'ir.actions.act_window_close'}
        else:
            raise exceptions.UserError("Usted no tiene permitido cancelar ordenes abiertas")
