# © 2018 Eneldo Serrata <eneldo@marcos.do>

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
