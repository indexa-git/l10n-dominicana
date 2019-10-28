import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    ncf = fields.Char(
        string="NCF",
    )
    ncf_origin_out = fields.Char(
        "Affects",
    )
    ncf_expiration_date = fields.Date(
        string="NCF expiration date",
    )
    fiscal_type_id = fields.Many2one(
        'account.fiscal.type',
        string="Fiscal Type",
    )
    fiscal_sequence_id = fields.Many2one(
        'account.fiscal.sequence',
        string="Fiscal Sequence",
        copy=False,
    )
    is_used_in_order = fields.Boolean(
        default=False
    )

    @api.model
    def _order_fields(self, ui_order):
        """
        Prepare the dict of values to create the new pos order.
        """
        fields = super(PosOrder, self)._order_fields(ui_order)
        fields['ncf'] = ui_order['ncf']
        fields['ncf_origin_out'] = ui_order['ncf_origin_out']
        fields['ncf_expiration_date'] = ui_order['ncf_expiration_date']
        fields['fiscal_type_id'] = ui_order['fiscal_type_id']
        fields['fiscal_sequence_id'] = ui_order['fiscal_sequence_id']

        return fields

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a pos order.
        """
        invoice_vals = super(PosOrder, self)._prepare_invoice()
        if self.config_id.invoice_journal_id.fiscal_journal:
            invoice_vals['reference'] = self.ncf
            invoice_vals['origin_out'] = self.ncf_origin_out
            invoice_vals['ncf_expiration_date'] = self.ncf_expiration_date
            invoice_vals['fiscal_type_id'] = self.fiscal_type_id.id
            invoice_vals['fiscal_sequence_id'] = self.fiscal_sequence_id.id

        return invoice_vals

    # TODO: this part is for credit note
    @api.model
    def _payment_fields(self, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(ui_paymentline)

        fields.update({
            'note': ui_paymentline.get('returned_ncf'),
        })

        return fields

    def _prepare_bank_statement_line_payment_values(self, data):

        args = super(PosOrder, self)\
            ._prepare_bank_statement_line_payment_values(data)

        if 'note' in data:
            args.update({
                'note': data['note']
            })

        return args

    @api.multi
    def _create_order_payments(self):
        # create all orders payment from statements
        for order in self:
            if order.config_id.invoice_journal_id.fiscal_journal:
                for statement in order.statement_ids:
                    # TODO: his part is for return order (credits notes)
                    if statement.journal_id.is_for_credit_notes:
                        # Note in statement line is equals to returned_ncf
                        # (NCF credit note)
                        credit_note_order = self.env['pos.order']\
                            .search([('ncf', '=', statement.note)])
                        if not credit_note_order:
                            raise UserError(_('Credit note not exist'))

                        if credit_note_order.invoice_id.state == 'paid':
                            raise UserError(
                                _('The credit note used in another invoice,'
                                  ' please unlink that invoice.')
                            )
                        credit_note_order.update({
                            'is_used_in_order': True
                        })
                        lines = credit_note_order.invoice_id.move_id.line_ids
                        statement.update({
                            'move_name':
                                credit_note_order.invoice_id.move_name,
                            'journal_entry_ids':
                                (4, [line.id for line in lines])
                        })
                        order._reconcile_refund_invoice(
                            credit_note_order.invoice_id
                        )
                    else:
                        statement.sudo().fast_counterpart_creation()

                    if not statement.journal_entry_ids.ids:
                        raise UserError(
                            _('All the account entries lines must be processed'
                              ' in order to close the statement.')
                        )

    @api.multi
    def action_pos_order_invoice_no_return_pdf(self):
        invoice = self.env['account.invoice']
        for order in self:
            # Force company for all SUPERUSER_ID action
            local_context = dict(
                self.env.context,
                force_company=order.company_id.id,
                company_id=order.company_id.id)

            if order.invoice_id:
                invoice += order.invoice_id
                continue

            if not order.partner_id:
                if not order.config_id.default_partner_id:
                    raise UserError(
                        _('This point of sale not have default customer,'
                          ' please set default customer in config POS'))
                order.write({
                    'partner_id': order.config_id.default_partner_id.id
                })

            invoice = invoice.new(order._prepare_invoice())
            invoice.is_from_pos = True
            invoice._onchange_partner_id()
            invoice.fiscal_position_id = order.fiscal_position_id

            inv = invoice._convert_to_write({
                name: invoice[name] for name in invoice._cache
            })
            new_invoice = invoice\
                .with_context(local_context).sudo().create(inv)
            message = _("This invoice has been created from the point of sale "
                        "session: <a href=# data-oe-model=pos.order "
                        "data-oe-id=%d>%s</a>") % (order.id, order.name)
            new_invoice.message_post(body=message)
            order.sudo().write({
                'invoice_id': new_invoice.id,
                'state': 'invoiced'
            })
            invoice += new_invoice

            for line in order.lines:
                self.with_context(local_context)._action_create_invoice_line(
                    line,
                    new_invoice.id
                )
            new_invoice.with_context(local_context).sudo().compute_taxes()
            order.sudo().write({'state': 'invoiced'})

    @api.model
    def _process_order(self, pos_order):
        """
        this part is using for eliminate cash return
        :param pos_order:
        :return:
        """
        if pos_order['amount_return'] > 0:

            pos_session_obj = self.env['pos.session'].browse(
                pos_order['pos_session_id']
            )
            cash_journal_id = pos_session_obj.cash_journal_id.id
            if not cash_journal_id:
                # If none, select for change one of the cash journals of the PO
                # This is used for example when a customer pays by credit card
                # an amount higher than total amount of the order and gets cash
                # back
                cash_journal = [statement.journal_id
                                for statement in pos_session_obj.statement_ids
                                if statement.journal_id.type == 'cash']
                if not cash_journal:
                    raise UserError(
                        _("No cash statement found for this session. "
                          "Unable to record returned cash."))

                cash_journal_id = cash_journal[0].id

            for index, statement in enumerate(pos_order['statement_ids']):

                if statement[2]['journal_id'] == cash_journal_id:
                    pos_order['statement_ids'][index][2]['amount'] = \
                        statement[2]['amount'] - pos_order['amount_return']

            pos_order['amount_return'] = 0

        return super(PosOrder, self)._process_order(pos_order)

    @api.model
    def create_from_ui(self, orders):

        res = super(PosOrder, self).create_from_ui(orders)

        order_list = []
        if type(res) is 'DictType':
            order_list = res['orders']
        else:
            for re in res:
                order_list.append({'id': re})

        for order in order_list:

            order_obj = self.env['pos.order'].search([
                ('id', '=', order['id'])
            ])
            if order_obj.config_id.invoice_journal_id.fiscal_journal \
                    and order_obj.state != 'invoiced':

                order_obj.action_pos_order_invoice_no_return_pdf()
                order_obj.invoice_id.sudo().action_invoice_open()

                # TODO: THIS PART IS FOR OFFLINE MODE
                # if order_obj.invoice_id.name != order_obj.move_name:
                #     raise UserError(_(
                #         u'El número de comprobante fiscal posee un error, '
                #           u'favor contacte al administrador: I:'
                #           + order_obj.invoice_id.name + u' vs P:'
                #           + order_obj.move_name)
                #     )

                order_obj.sudo()._create_order_payments()
                order_obj.sudo()._reconcile_payments()
                order_obj.account_move = order_obj.invoice_id.move_id
                if not order_obj.picking_id:
                    order_obj.create_picking()

        return res

    # For returns orders (nota de credito)

    def _reconcile_refund_invoice(self, refund_invoice):
        invoice = self.invoice_id
        movelines = invoice.move_id.line_ids
        to_reconcile_ids = {}
        to_reconcile_lines = self.env['account.move.line']
        for line in movelines:
            if line.account_id.id == invoice.account_id.id:
                to_reconcile_lines += line
                to_reconcile_ids.setdefault(line.account_id.id, []).append(
                    line.id)
            if line.reconciled:
                line.remove_move_reconcile()
        for tmpline in refund_invoice.move_id.line_ids:
            if tmpline.account_id.id == invoice.account_id.id:
                to_reconcile_lines += tmpline
        to_reconcile_lines.filtered(lambda l: not l.reconciled).reconcile()

    @api.multi
    def return_from_ui(self, orders):
        super(PosOrder, self).return_from_ui(orders)
        for tmp_order in orders:
            # eliminates the return of the order several times at the same time
            returned_order = self.search([
                ('pos_reference', '=', tmp_order['data']['name']),
                ('date_order', '=', tmp_order['data']['creation_date']),
                ('returned_order', '=', True)
            ])

            if returned_order.state == 'draft' and \
                    returned_order.config_id.invoice_journal_id.fiscal_journal:

                returned_order.create_pos_order_refund_invoice()
                returned_order.invoice_id.sudo().action_invoice_open()
                # TODO: this part is for offline mode
                # if returned_order.invoice_id.name !=returned_order.move_name:
                #     raise UserError(_(
                #         u'El número de comprobante fiscal posee un error, '
                #         u'favor contacte al administrador: I:'
                #         + returned_order.invoice_id.name + u' vs P:'
                #         + returned_order.move_name
                #     ))
                returned_order.account_move = returned_order.invoice_id.move_id
                if not returned_order.picking_id:
                    returned_order.create_picking()

    def create_pos_order_refund_invoice(self):

        origin_order = self.search([('ncf', '=', self.ncf_origin_out)])

        if origin_order:

            origin_invoice = origin_order.invoice_id

            if origin_invoice.state in ['draft', 'proforma2', 'cancel']:
                raise UserError(
                    _('Cannot refund draft/proforma/cancelled invoice.')
                )

            refund_invoice = origin_invoice.refund(
                fields.Date.to_date(self.date_order),
                fields.Date.to_date(self.date_order),
                self.name,
                self.session_id.config_id.invoice_journal_id.id
            )

            refund_invoice.write({
                'reference': self.ncf,
                'origin_out': self.ncf_origin_out,
                'ncf_expiration_date': self.ncf_expiration_date,
                'fiscal_type_id': self.fiscal_type_id.id,
                'fiscal_sequence_id': self.fiscal_sequence_id.id,
            })

            # TODO: es probable que las lineas tengan el mismo producto
            # pero con diferentes precios, queda pendeiente buscar una
            # solucion futura para este preoblema

            products_ids = []

            for refund_invoice_line in refund_invoice.invoice_line_ids:
                if refund_invoice_line.product_id.id in products_ids:
                    refund_invoice_line.sudo().unlink()
                else:
                    products_ids.append(refund_invoice_line.product_id.id)

            for refund_invoice_line in refund_invoice.invoice_line_ids:

                product = refund_invoice_line.product_id
                refund_order_lines = self.lines.filtered(
                    lambda line: line.product_id.id == product.id
                )

                if refund_order_lines:

                    total_quantity = 0

                    for refund_order_line in refund_order_lines:
                        total_quantity = total_quantity + refund_order_line.qty

                    refund_invoice_line.write({
                        'quantity': abs(total_quantity)
                    })

                else:

                    refund_invoice_line.sudo().unlink()

            refund_invoice.write({'is_from_pos': True})
            refund_invoice.compute_taxes()

            if round(refund_invoice.amount_total, -2) != \
                    round(abs(self.amount_total), -2):
                raise UserError(_(
                    'Credit note has error please contact your manager '
                    + str(refund_invoice.amount_total) + ' '
                    + str(self.amount_total)))

            # TODO: this part is used for cancel invoice with credit note
            # movelines = origin_invoice.move_id.line_ids
            # to_reconcile_ids = {}
            # to_reconcile_lines = self.env['account.move.line']
            # to_reconcile_lines_from_payments = self.env['account.move.line']
            # to_reconcile_lines_from_credit_notes =\
            #     self.env['account.move.line']
            #
            # for line in movelines:
            #     if line.account_id.id == origin_invoice.account_id.id:
            #         to_reconcile_lines += line
            #         to_reconcile_lines_from_payments += line
            #         to_reconcile_lines_from_credit_notes += line
            #         to_reconcile_ids.setdefault(line.account_id.id, [])\
            #             .append(line.id)
            #     if line.reconciled:
            #         for matched_credit in line.matched_credit_ids:
            #             if matched_credit.credit_move_id.payment_id:
            #                 to_reconcile_lines_from_payments \
            #                     += matched_credit.credit_move_id
            #             if matched_credit.credit_move_id.invoice_id:
            #                 to_reconcile_lines_from_credit_notes \
            #                     += matched_credit.credit_move_id
            #
            #         line.remove_move_reconcile()

            refund_invoice.write({'is_from_pos': True})

            # TODO: this part is for offline mode
            # if refund_invoice.name != self.move_name:
            #     raise UserError(_(
            #         u'El número de comprobante fiscal posee '
            #         u'un error, favor contacte al administrador '
            #         u'I:' + refund_invoice.name + u' vs P:'
            #         + self.move_name
            #     ))
            # TODO: this part is used for cancel invoice with credit note
            # for tmpline in refund_invoice.move_id.line_ids:
            #     if tmpline.account_id.id == origin_invoice.account_id.id:
            #         to_reconcile_lines += tmpline
            #
            # to_reconcile_lines\
            #     .filtered(lambda l: l.reconciled == False).reconcile()
            #
            # if len(to_reconcile_lines_from_credit_notes) > 1:
            #     to_reconcile_lines_from_credit_notes\
            #         .filtered(lambda l: l.reconciled == False).reconcile()
            #
            # if len(to_reconcile_lines_from_payments) > 1:
            #     to_reconcile_lines_from_payments\
            #         .filtered(lambda l: l.reconciled == False).reconcile()

            self.sudo().write({
                'invoice_id': refund_invoice.id,
                'state': 'invoiced',
            })

        else:

            raise UserError(
                _('Order not found, pleas contact your manager')
            )
