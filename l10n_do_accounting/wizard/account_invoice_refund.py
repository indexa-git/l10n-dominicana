

from odoo import models, fields


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    refund_type = fields.Selection([
        ('full_refund', 'Full Refund'),
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Amount'),
    ],
        default='full_refund',
    )
