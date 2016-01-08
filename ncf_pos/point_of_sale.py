# -*- coding: utf-8 -*-
from openerp import models, fields, api,exceptions

import time


class PosOrder(models.Model):
    _inherit = "pos.order"

    partner_id = fields.Many2one('res.partner', 'Customer', select=1,
                                 states={'draft': [('readonly', False)], 'paid': [('readonly', False)]})
    fiscal_position_id = fields.Many2one('account.fiscal.position', 'Fiscal Position',
                                         domain=[('supplier', '=', False)])
    session_id = fields.Many2one('pos.session', 'Session',
                                        required=True,
                                        select=1,
                                        domain="[('state', '=', 'opened')]",
                                        states={'draft' : [('readonly', False)]},
                                        readonly=True)
    reserve_ncf_seq = fields.Char(size=19)

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

        if fiscal_type == 'fiscal':
            sequence = self.sale_journal.fiscal_sequence_id
        elif fiscal_type == 'gov':
            sequence = self.sale_journal.gov_sequence_id
        elif fiscal_type == 'special':
            sequence = self.sale_journal.special_sequence_id
        else:
            sequence = self.sale_journal.final_sequence_id

        date_order = self.date_order.split(" ")[0]
        self.reserve_ncf_seq = sequence.with_context(ir_sequence_date=date_order).next_by_id()

    def generate_ncf_invoice(self):
        self.write({'state': 'paid'})
        self.create_picking()
        self.action_invoice()
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

            self.env["account.move.line.reconcile.writeoff"].with_context(active_ids=move_line_ids).trans_rec_reconcile_partial()

    @api.model
    def get_ncf(self, name):
        ncf = False
        while not ncf:
            time.sleep(1)
            ncf = self.search([('pos_reference','=',name)]).reserve_ncf_seq
            self._cr.commit()
        return {"ncf": ncf}


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
