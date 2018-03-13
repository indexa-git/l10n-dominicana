from odoo import models, fields, api, _
class Invoices(models.Model):    
    _inherit = "account.invoice"    

    @api.model
        def order_search_from_ui(self, input_txt):
            invoice_ids = self.env["account.invoice"].search([('number', 'ilike', "%{}%".format(input_txt))], limit=100)
            order_ids = self.search([('invoice_id', 'in', invoice_ids.ids)])
            return invoice_ids