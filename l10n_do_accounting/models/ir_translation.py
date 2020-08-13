# -*- coding: utf-8 -*-
from odoo import models


class IrTraslation(models.Model):
    _inherit = 'ir.translation'

    def init(self):
        all_traslation_employee_payslips = self.search([
            ('lang', '=', 'es_DO'),
            ('src', '=', 'Credit Note'),
        ])
        for traslation_employee_payslip in all_traslation_employee_payslips:
            traslation_employee_payslip.update({
                'value': u'Nota de crédito',
            })

        # all_traslation_payslyp_batches = self.search([
        #     ('lang', '=', 'es_DO'),
        #     ('src', '=', 'Payslips Batches'),
        # ])
        # for traslation_payslip_batches in all_traslation_payslyp_batches:
        #     traslation_payslip_batches.update({
        #         'value': 'Nómina Colectiva',
        #     })
