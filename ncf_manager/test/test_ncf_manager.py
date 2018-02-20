# -*- coding: utf-8 -*-

from odoo.tests import common


class TestDgiiValidators(common.TransactionCase):

    def test_create_res_partner_with_cedula_on_name(self):
        res = self.env['project.project'].create({"name": "00111616876"})
        self.assertEqual(res.vat, '00111616876')

    def test_create_res_partner_with_rnc_on_name(self):
        res = self.env['project.project'].create({"name": "101733934"})
        self.assertEqual(res.vat, '101733934')

    def test_create_res_partner_with_cedula_on_vat(self):
        res = self.env['project.project'].create({"vat": "00111616876"})
        self.assertEqual(res.vat, '00111616876')

    def test_create_res_partner_with_rnc_on_vat(self):
        res = self.env['project.project'].create({"vat": "101733934"})
        self.assertEqual(res.vat, '101733934')
