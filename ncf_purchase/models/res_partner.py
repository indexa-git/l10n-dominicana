# © 2018 Manuel Marquez <buzondemam@gmail.com>

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
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_journal_id = fields.Many2one('account.journal',
                                          company_dependent=True,
                                          domain=[('type', '=', 'purchase')])
