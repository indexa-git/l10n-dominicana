# © 2019 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>

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

from odoo.addons.point_of_sale.wizard.pos_box import PosBox
from odoo import api


class PosBoxOut(PosBox):

    _inherit = "cash.box.out"

    @api.model
    def default_get(self, fields):
        data = self._context
        res = super(PosBoxOut, self).default_get(fields)
        pos_session = self.env[data['active_model']].browse(data['active_id'])
        date = pos_session.start_at
        res.update({
            'name': pos_session.config_id.name + ' ' + str(date)
        })
        return res
