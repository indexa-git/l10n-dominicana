# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions

import time
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.osv import osv


class pos_session(osv.osv):
    _inherit = ['pos.session','mail.thread', 'ir.needaction_mixin']
    _name = "pos.session"

    def _confirm_orders(self, cr, uid, ids, context=None):
        pos_order_obj = self.pool.get('pos.order')
        for session in self.browse(cr, uid, ids, context=context):
            company_id = session.config_id.journal_id.company_id.id
            local_context = dict(context or {}, force_company=company_id)
            order_ids = [order.id for order in session.order_ids if order.state == 'paid']

            move_id = pos_order_obj._create_account_move(cr, uid, session.start_at, session.name, session.config_id.journal_id.id, company_id, context=context)

            pos_order_obj._create_account_move_line(cr, uid, order_ids, session, move_id, context=local_context)

            for order in session.order_ids:
                if order.state == 'done':
                    continue
                if order.state not in ('paid', 'invoiced', 'cancel'):
                    raise exceptions.UserError(_("You cannot confirm all orders of this session, because they have not the 'paid' status"))
                else:
                    pos_order_obj.signal_workflow(cr, uid, [order.id], 'done')

        return True


class PosOrder(models.Model):
    _inherit = ["pos.order", 'mail.thread', 'ir.needaction_mixin']
    _name = 'pos.order'

    partner_id = fields.Many2one('res.partner', 'Customer', select=1,
                                 states={'draft': [('readonly', False)], 'paid': [('readonly', False)]})
    fiscal_position_id = fields.Many2one('account.fiscal.position', 'Fiscal Position',
                                         domain=[('supplier', '=', False)])
    session_id = fields.Many2one('pos.session', 'Session',
                                 required=True,
                                 select=1,
                                 domain="[('state', '=', 'opened')]",
                                 states={'draft': [('readonly', False)]},
                                 readonly=True)
    reserve_ncf_seq = fields.Char(size=19)
    origin = fields.Many2one("pos.order", string="Afecta")
    why_cancel = fields.Char("Concepto de cancelacion")
    state = fields.Selection([('draft', 'New'),
                              ('cancel', 'Cancelled'),
                              ('paid', 'Paid'),
                              ('done', 'Posted'),
                              ('invoiced', 'Invoiced'),
                              ('refund', u"Nota De Crédito"),
                              ('refund_money', u"Nota De Crédito Con Devolucion De Efectivo")],
                             'Status', readonly=True, copy=False)

    @api.onchange("session_id")
    def onchange_session_id(self):
        self.partner_id = self.session_id.config_id.default_partner_id.id
        self.pricelist_id = self.partner_id.property_product_pricelist.id
        self.fiscal_position_id = self.partner_id.property_account_position_id.id

    @api.onchange("partner_id")
    def _onchange_partner_id(self, part=False):
        if self.partner_id:
            self.fiscal_position_id = self.partner_id.property_account_position_id.id

    @api.onchange("fiscal_position_id")
    def onchange_fiscal_position_id(self):
        if self.fiscal_position_id and self.partner_id.property_account_position_id.id != self.fiscal_position_id:
            self.partner_id.write({"property_account_position_id": self.fiscal_position_id.id})

    @api.model
    def create_from_ui(self, orders):
        res = super(PosOrder, self).create_from_ui(orders)
        for order_id in res:
            self.browse(order_id).set_reserve_ncf_seq()
            self.env.cr.commit()
            self.browse(order_id).generate_ncf_invoice()
        return res

    @api.model
    def action_paid(self):
        if not self.pos_reference:
            self.set_reserve_ncf_seq()
            self.generate_ncf_invoice()

        return True

    def set_reserve_ncf_seq(self):
        if not self.partner_id:
            self.partner_id = self.session_id.config_id.default_partner_id.id

        fiscal_type = self.partner_id.property_account_position_id.client_fiscal_type

        if self.amount_total < 0:
            sequence = self.sale_journal.refund_sequence_id
        elif fiscal_type == 'fiscal':
            sequence = self.sale_journal.fiscal_sequence_id
        elif fiscal_type == 'gov':
            sequence = self.sale_journal.gov_sequence_id
        elif fiscal_type == 'special':
            sequence = self.sale_journal.special_sequence_id
        else:
            sequence = self.sale_journal.final_sequence_id

        date_order = self.date_order.split(" ")[0]
        self.reserve_ncf_seq = sequence.with_context(ir_sequence_date=date_order).next_by_id()

    @api.multi
    def refund(self):
        """Create a copy of order for refund order"""
        clone_list = []

        for order in self:
            current_session_ids = self.env['pos.session'].search(
                    [('state', '!=', 'closed'), ('user_id', '=', self._uid)])
            if not current_session_ids:
                raise exceptions.UserError(
                    _('To return product(s), you need to open a session that will be used to register the refund.'))

            clone_id = self.copy({'name': order.name + ' REFUND', 'session_id': current_session_ids[0].id,
                                  'date_order': time.strftime('%Y-%m-%d %H:%M:%S'), 'origin': order.id, "lines": False})

            new_lines = []
            for line in order.lines:
                if not line.qty_allow_refund == 0:
                    ln = (0, False, {'company_id': line.company_id.id,
                                                 'name': line.name,
                                                 'notice': line.notice,
                                                 'product_id': line.product_id.id,
                                                 'price_unit': line.price_unit,
                                                 'qty': line.qty*-1,
                                                 'discount': line.discount,
                                                 'order_id': clone_id.id,
                                                 'tax_ids': [t.id for t in line.tax_ids],
                                                 'qty_allow_refund': line.qty_allow_refund,
                                                 'refund_line_ref': line.id
                                                 })

                new_lines.append(ln)

            if not new_lines:
                raise exceptions.UserError("Todos los productos de esta orden ya fueron devueltas!")
            clone_id.write({"lines": new_lines})
            clone_list.append(clone_id)

        abs = {
            'name': _('Devolucion de productos'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id':clone_list[0].id,
            'view_id': False,
            'context': self._context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        return abs

    def generate_ncf_invoice(self):

        self.write({'state': 'paid'})
        self._cr.execute("update pos_order_line set qty_allow_refund = qty where order_id = {}".format(self.id))
        self.action_invoice()
        self.create_picking()
        self.invoice_id.move_name = self.reserve_ncf_seq
        self.invoice_id.signal_workflow("invoice_open")
        self.action_paid_reconcile()

    @api.model
    def action_paid_reconcile(self):
        move_line_ids = []
        for rec in self:
            for st in rec.statement_ids:
                st.fast_counterpart_creation()
                for move in st.journal_entry_ids:
                    for line in move.line_ids:
                        if line.credit > 0:
                            move_line_ids.append(line.id)
            for line in rec.invoice_id.move_id.line_ids:
                if line.debit > 0:
                    move_line_ids.append(line.id)

            self.env["account.move.line.reconcile.writeoff"].with_context(
                active_ids=move_line_ids).trans_rec_reconcile_partial()

    @api.model
    def get_ncf(self, name):
        ncf = False
        while not ncf:
            time.sleep(1)
            ncf = self.search([('pos_reference', '=', name)]).reserve_ncf_seq
            self._cr.commit()
        return {"ncf": ncf}


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    qty_allow_refund = fields.Float(string='qty allow refund', digits=dp.get_precision('Product Unit of Measure'), copy=False, required=False)
    refund_line_ref = fields.Many2one("pos.order.line", string="origin line refund", copy=False)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_partner_id = fields.Many2one("res.partner", string="Cliente de contado")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_from_ui(self, partner):
        """ create or modify a partner from the point of sale ui.
            partner contains the partner's fields. """
        # image is a dataurl, get the data after the comma
        if partner.get('image', False):
            img = partner['image'].split(',')[1]
            partner['image'] = img

        property_account_position_id = partner.get("property_account_position_id", False)
        if property_account_position_id:
            partner.update({"property_account_position_id": int(property_account_position_id)})

        if partner.get('id', False):  # Modifying existing partner
            partner_id = partner['id']
            del partner['id']
            self.browse(partner_id).write(partner)
        else:
            partner_id = self.create(partner)

        return partner_id.id
