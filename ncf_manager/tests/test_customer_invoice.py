# © 2018 José López <jlopez@indexa.do>

# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

import random
from odoo.tests.common import TransactionCase


class InvoiceNCFSequenceTest(TransactionCase):

    def setUp(self):
        super(InvoiceNCFSequenceTest, self).setUp()

        self.inv_obj = self.env['account.invoice']
        self.payment_term = self.env.ref(
            'account.account_payment_term_immediate')
        self.account = self.env.ref('l10n_do.1_do_niif_11030201')

        # Setup Fiscal journal
        self.journal = self.env['account.journal'].create({
            'name': 'Sale Journal',
            'type': 'sale',
            'ncf_control': True,
            'code': 'SJ'
        })
        self.journal.ncf_control = True
        self.journal.create_ncf_sequence()

        self.product_consu = self.env.ref('product.product_delivery_01')
        self.product_service = self.env.ref('product.product_product_1')

        self.invoice_line_ids = [
            (0, 0, {
                'product_id': self.product_consu.id,
                'quantity': 10.0,
                'account_id': self.env['account.account'].search(
                    [('user_type_id', '=',
                      self.env.ref('account.data_account_type_revenue').id)],
                    limit=1).id,
                'name': 'test product consu',
                'price_unit': 100.00,
                'invoice_line_tax_ids': [
                    (4, self.env.ref('l10n_do.1_tax_18_sale').id)
                ]
            }),
            (0, 0, {
                'product_id': self.product_service.id,
                'quantity': 10.0,
                'account_id': self.env['account.account'].search(
                    [('user_type_id', '=',
                      self.env.ref('account.data_account_type_revenue').id)],
                    limit=1).id,
                'name': 'test product consu',
                'price_unit': 100.00,
                'invoice_line_tax_ids': [
                    (4, self.env.ref('l10n_do.1_tax_18_sale').id)
                ]
            })
        ]

        self.fiscal_partners = [
            self.env.ref('ncf_manager.res_partner_demo_1'),
            self.env.ref('ncf_manager.res_partner_demo_2'),
            self.env.ref('ncf_manager.res_partner_demo_3'),
            self.env.ref('ncf_manager.res_partner_demo_4')
        ]

        self.final_partners = [
            self.env.ref('ncf_manager.res_partner_demo_5'),
            self.env.ref('ncf_manager.res_partner_demo_6')
        ]

        self.gov_partners = [
            self.env.ref('ncf_manager.res_partner_demo_7'),
            self.env.ref('ncf_manager.res_partner_demo_8')
        ]

        self.special_partners = [
            self.env.ref('ncf_manager.res_partner_demo_9'),
            self.env.ref('ncf_manager.res_partner_demo_10')
        ]

        self.export_partners = [
            self.env.ref('ncf_manager.res_partner_demo_11'),
            self.env.ref('ncf_manager.res_partner_demo_12')
        ]

        self.sale_fiscal_type = [
            t[0] for t in
            self.env["res.partner"]._fields['sale_fiscal_type'].selection
        ]

    def test_journal(self):
        """ Fiscal Journal tests """

        # Check if journal even exists
        assert self.journal

        # Check if ncf_control = True
        self.assertTrue(self.journal.ncf_control,
                        "Journal has not ncf_control activated")

        sequence_id = self.journal.sequence_id

        # Check if both journal and sequence have ncf_control
        self.assertEquals(self.journal.ncf_control, sequence_id.ncf_control)

        # Check if all sale_fiscal_type sequence created
        self.assertEquals(
            len([
                x for x in sequence_id.date_range_ids
                if x.sale_fiscal_type in self.sale_fiscal_type
            ]), len(self.sale_fiscal_type),
            "Not all sequence date range created.")

    def test_fiscal_invoices(self):
        """ Credito Fiscal NCF tests """

        n = 100

        # Loop n times so NCF sequence is tested on a high demand scenario
        for i in range(n):
            partner_id = random.choice(self.fiscal_partners)

            invoice_id = self.inv_obj.create({
                'type': 'out_invoice',
                'partner_id': partner_id.id,
                'account_id': self.account.id,
                'sale_fiscal_type': partner_id.sale_fiscal_type,
                'payment_term_id': self.payment_term.id,
                'journal_id': self.journal.id,
                'income_type': '01',
                'invoice_line_ids': self.invoice_line_ids
            })

            # Check sale_fiscal_type = fiscal
            self.assertEquals(invoice_id.sale_fiscal_type, 'fiscal')

            # Validate invoice
            invoice_id.action_invoice_open()

            date_range_id = self.env['ir.sequence.date_range'].search([
                ('sale_fiscal_type', '=', partner_id.sale_fiscal_type),
                ('sequence_id', '=', self.journal.sequence_id.id)
            ])

            # Check if there is only one date_rage for this sale_fiscal_type
            self.assertEquals(len(date_range_id), 1)

            # Check if fiscal NCF
            self.assertEquals(str(invoice_id.reference)[:3], 'B01')

            # Check date_range sequence
            self.assertEquals(int(str(invoice_id.reference)[3:]),
                              date_range_id.number_next - 1)

    def test_final_invoices(self):
        """ Consumo NCF tests """

        n = 100

        # Loop n times so NCF sequence is tested on a high demand scenario
        for i in range(n):
            partner_id = random.choice(self.final_partners)

            invoice_id = self.inv_obj.create({
                'type': 'out_invoice',
                'partner_id': partner_id.id,
                'account_id': self.account.id,
                'sale_fiscal_type': partner_id.sale_fiscal_type,
                'payment_term_id': self.payment_term.id,
                'journal_id': self.journal.id,
                'income_type': '01',
                'invoice_line_ids': self.invoice_line_ids
            })

            # Check sale_fiscal_type = final
            self.assertEquals(invoice_id.sale_fiscal_type, 'final')

            # Validate invoice
            invoice_id.action_invoice_open()

            date_range_id = self.env['ir.sequence.date_range'].search([
                ('sale_fiscal_type', '=', partner_id.sale_fiscal_type),
                ('sequence_id', '=', self.journal.sequence_id.id)
            ])

            # Check if there is only one date_rage for this sale_fiscal_type
            self.assertEquals(len(date_range_id), 1)

            # Check if final NCF
            self.assertEquals(str(invoice_id.reference)[:3], 'B02')

            # Check date_range sequence
            self.assertEquals(int(str(invoice_id.reference)[3:]),
                              date_range_id.number_next - 1)

    def test_gov_invoices(self):
        """ Gubernamentales NCF tests """

        n = 100

        # Loop n times so NCF sequence is tested on a high demand scenario
        for i in range(n):
            partner_id = random.choice(self.gov_partners)

            invoice_id = self.inv_obj.create({
                'type': 'out_invoice',
                'partner_id': partner_id.id,
                'account_id': self.account.id,
                'sale_fiscal_type': partner_id.sale_fiscal_type,
                'payment_term_id': self.payment_term.id,
                'journal_id': self.journal.id,
                'income_type': '01',
                'invoice_line_ids': self.invoice_line_ids
            })

            # Check sale_fiscal_type = gov
            self.assertEquals(invoice_id.sale_fiscal_type, 'gov')

            # Validate invoice
            invoice_id.action_invoice_open()

            date_range_id = self.env['ir.sequence.date_range'].search([
                ('sale_fiscal_type', '=', partner_id.sale_fiscal_type),
                ('sequence_id', '=', self.journal.sequence_id.id)
            ])

            # Check if there is only one date_rage for this sale_fiscal_type
            self.assertEquals(len(date_range_id), 1)

            # Check if gov NCF
            self.assertEquals(str(invoice_id.reference)[:3], 'B15')

            # Check date_range sequence
            self.assertEquals(int(str(invoice_id.reference)[3:]),
                              date_range_id.number_next - 1)

    def test_special_invoices(self):
        """ Regimenes Especiales NCF tests """

        n = 100

        # Loop n times so NCF sequence is tested on a high demand scenario
        for i in range(n):
            partner_id = random.choice(self.special_partners)

            invoice_id = self.inv_obj.create({
                'type': 'out_invoice',
                'partner_id': partner_id.id,
                'account_id': self.account.id,
                'sale_fiscal_type': partner_id.sale_fiscal_type,
                'payment_term_id': self.payment_term.id,
                'journal_id': self.journal.id,
                'income_type': '01',
                'invoice_line_ids': self.invoice_line_ids
            })

            # Check sale_fiscal_type = special
            self.assertEquals(invoice_id.sale_fiscal_type, 'special')

            # Because of Norma 05-19, remove taxes from Regímenes Especiales
            # invoices
            invoice_id.tax_line_ids = [(5, 0, 0)]

            # Validate invoice
            invoice_id.action_invoice_open()

            date_range_id = self.env['ir.sequence.date_range'].search([
                ('sale_fiscal_type', '=', partner_id.sale_fiscal_type),
                ('sequence_id', '=', self.journal.sequence_id.id)
            ])

            # Check if there is only one date_rage for this sale_fiscal_type
            self.assertEquals(len(date_range_id), 1)

            # Check if special NCF
            self.assertEquals(str(invoice_id.reference)[:3], 'B14')

            # Check date_range sequence
            self.assertEquals(int(str(invoice_id.reference)[3:]),
                              date_range_id.number_next - 1)

    def test_unico_invoices(self):
        """ Unico Ingreso NCF tests """

        n = 100

        # Loop n times so NCF sequence is tested on a high demand scenario
        for i in range(n):
            partner_id = random.choice(self.special_partners)

            invoice_id = self.inv_obj.create({
                'type': 'out_invoice',
                'partner_id': partner_id.id,
                'account_id': self.account.id,
                'sale_fiscal_type': 'unico',
                'payment_term_id': self.payment_term.id,
                'journal_id': self.journal.id,
                'income_type': '01',
                'invoice_line_ids': self.invoice_line_ids
            })

            # Check sale_fiscal_type = unico
            self.assertEquals(invoice_id.sale_fiscal_type, 'unico')

            # Validate invoice
            invoice_id.action_invoice_open()

            date_range_id = self.env['ir.sequence.date_range'].search([
                ('sale_fiscal_type', '=', 'unico'),
                ('sequence_id', '=', self.journal.sequence_id.id)
            ])

            # Check if there is only one date_rage for this sale_fiscal_type
            self.assertEquals(len(date_range_id), 1)

            # Check if unico NCF
            self.assertEquals(str(invoice_id.reference)[:3], 'B12')

            # Check date_range sequence
            self.assertEquals(int(str(invoice_id.reference)[3:]),
                              date_range_id.number_next - 1)

    def test_cross_fiscal_type_invoices(self):
        """ Cross Fiscal Type NCF tests """

        n = 100
        ncf_prefix_map = {
            'final': 'B02',
            'fiscal': 'B01',
            'gov': 'B15',
            'special': 'B14',
            'unico': 'B12',
            'export': 'B16',
        }

        # Loop n times so NCF sequence is tested on a high demand scenario
        for i in range(n):
            partner_id = random.choice(self.fiscal_partners +
                                       self.final_partners +
                                       self.gov_partners +
                                       self.special_partners +
                                       self.export_partners)

            invoice_id = self.inv_obj.create({
                'type': 'out_invoice',
                'partner_id': partner_id.id,
                'account_id': self.account.id,
                'sale_fiscal_type': partner_id.sale_fiscal_type,
                'payment_term_id': self.payment_term.id,
                'journal_id': self.journal.id,
                'income_type': '01',
                'invoice_line_ids': self.invoice_line_ids
            })

            # Check invoice sale_fiscal_type = partner sale_fiscal_type
            self.assertEquals(invoice_id.sale_fiscal_type,
                              partner_id.sale_fiscal_type)

            # Because of Norma 05-19, remove taxes from Regímenes Especiales
            # invoices
            if partner_id in self.special_partners:
                invoice_id.tax_line_ids = [(5, 0, 0)]

            # Validate invoice
            invoice_id.action_invoice_open()

            date_range_id = self.env['ir.sequence.date_range'].search([
                ('sale_fiscal_type', '=', invoice_id.sale_fiscal_type),
                ('sequence_id', '=', self.journal.sequence_id.id)
            ])

            # Check if there is only one date_rage for this sale_fiscal_type
            self.assertEquals(len(date_range_id), 1)

            # Check if current sale_fiscal_type NCF
            self.assertEquals(
                str(invoice_id.reference)[:3],
                ncf_prefix_map[invoice_id.sale_fiscal_type])

            # Check date_range sequence
            self.assertEquals(int(str(invoice_id.reference)[3:]),
                              date_range_id.number_next - 1)

    def test_export_invoices(self):
        """ Exportaciones NCF tests """

        n = 100

        # Loop n times so NCF sequence is tested on a high demand scenario
        for i in range(n):
            partner_id = random.choice(self.export_partners)

            invoice_id = self.inv_obj.create({
                'type': 'out_invoice',
                'partner_id': partner_id.id,
                'account_id': self.account.id,
                'sale_fiscal_type': partner_id.sale_fiscal_type,
                'payment_term_id': self.payment_term.id,
                'journal_id': self.journal.id,
                'income_type': '01',
                'invoice_line_ids': self.invoice_line_ids
            })

            # Check sale_fiscal_type = fiscal
            self.assertEquals(invoice_id.sale_fiscal_type, 'export')

            # Validate invoice
            invoice_id.action_invoice_open()

            date_range_id = self.env['ir.sequence.date_range'].search([
                ('sale_fiscal_type', '=', partner_id.sale_fiscal_type),
                ('sequence_id', '=', self.journal.sequence_id.id)
            ])

            # Check if there is only one date_rage for this sale_fiscal_type
            self.assertEquals(len(date_range_id), 1)

            # Check if fiscal NCF
            self.assertEquals(str(invoice_id.reference)[:3], 'B16')

            # Check date_range sequence
            self.assertEquals(int(str(invoice_id.reference)[3:]),
                              date_range_id.number_next - 1)
