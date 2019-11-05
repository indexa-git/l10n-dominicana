

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    @api.model
    def _get_default_is_vendor_refund(self):
        if self._context.get('type') == 'in_invoice':
            return True
        return False

    @api.model
    def _default_account(self):
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale'),
             ('company_id', '=', self.env.user.company_id.id)], limit=1)
        if self._context.get('type') in ('out_invoice', 'in_refund'):
            return journal.default_credit_account_id.id
        return journal.default_debit_account_id.id

    refund_type = fields.Selection([
        ('full_refund', 'Full Refund'),
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Amount'),
    ],
        default='full_refund',
    )
    refund_method = fields.Selection([
        ('draft_refund', 'Create a draft credit note'),
        ('apply_refund', 'Create credit note and reconcile'),
    ],
        default='draft_refund',
        string="Credit Method",
    )
    percentage = fields.Float()
    amount = fields.Float()
    account_id = fields.Many2one(
        'account.account',
        string='Account',
        domain=[('deprecated', '=', False)],
        default=_default_account,
    )
    is_vendor_refund = fields.Boolean(
        default=_get_default_is_vendor_refund,
    )
    refund_reference = fields.Char()

    @api.onchange('refund_type')
    def onchange_refund_type(self):
        if self.refund_type != 'full_refund':
            self.filter_refund = 'refund'

    @api.multi
    def compute_refund(self, mode='refund'):
        xml_id = False
        created_inv = []
        for wizard in self:
            if wizard.refund_type == 'full_refund':
                return super(AccountInvoiceRefund, self).compute_refund(
                    mode=mode)

            inv_obj = self.env['account.invoice']
            context = dict(self._context or {})
            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state in ['draft', 'cancel']:
                    raise UserError(_(
                        'Cannot create credit note for the draft/cancelled '
                        'invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise UserError(_(
                        'Cannot create a credit note for the invoice which is '
                        'already reconciled, invoice should be unreconciled '
                        'first, then only you can add credit note for '
                        'this invoice.'))

                date = wizard.date or False
                description = wizard.description or inv.name
                refund_type = wizard.refund_type
                vendor_ref = wizard.refund_reference
                amount = wizard.amount if refund_type == 'fixed_amount' \
                    else inv.amount_untaxed * (wizard.percentage/100)
                refund = inv.with_context(
                    refund_type=wizard.refund_type,
                    amount=amount,
                    account=wizard.account_id.id,
                    vendor_ref=vendor_ref).refund(
                    wizard.date_invoice, date, description, inv.journal_id.id)

                if wizard.refund_method == 'apply_refund':
                    refund.action_invoice_open()
                    aml_id = refund._get_aml_for_register_payment()
                    inv.assign_outstanding_credit(aml_id.id)

                created_inv.append(refund.id)
                action_map = {'out_invoice': 'action_invoice_out_refund',
                              'out_refund': 'action_invoice_tree1',
                              'in_invoice': 'action_invoice_in_refund',
                              'in_refund': 'action_invoice_tree2'}
                xml_id = action_map[inv.type]
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            invoice_domain = safe_eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
        return True
