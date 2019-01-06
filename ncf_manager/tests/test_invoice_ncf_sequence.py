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

from odoo.tests.common import TransactionCase


class InvoiceNCFSequenceTest(TransactionCase):

    def setUp(self):
        super(InvoiceNCFSequenceTest, self).setUp()

        self.test_company = self.env['res.company'].create({'name': 'Test Company'})
        # Each test will check the number of rates for USD
        self.currency_usd = self.env.ref('base.USD')