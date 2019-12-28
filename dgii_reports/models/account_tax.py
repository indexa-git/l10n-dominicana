

from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    purchase_tax_type = fields.Selection(
        [('itbis', 'Paid ITBIS'),
         ('ritbis', 'Withheld ITBIS'),
         ('isr', 'Withheld ISR'),
         ('rext', 'Overseas payments (law 253-12)'),
         ('none', 'Non deductible')],
        default="none",
        string="Purchase Tax Type",
    )
    isr_retention_type = fields.Selection(
        [('01', 'Rentals'),
         ('02', 'Fees for Services'),
         ('03', 'Other Incomes'),
         ('04', 'Presumed Income'),
         ('05', 'Interest Paid to Legal Entities'),
         ('06', 'Interests Paid to Individuals'),
         ('07', 'Withholding by State Providers'),
         ('08', 'Mobile Games')],
        string="ISR Withholding Type",
    )
