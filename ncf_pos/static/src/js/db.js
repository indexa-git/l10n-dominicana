// © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
// © 2017 Gustavo Valverde <gustavo@iterativo.do>
// © 2018 Jorge Hernández <jhernandez@gruponeotec.com>

// This file is part of NCF Manager.

// NCF Manager is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// NCF Manager is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

odoo.define('ncf_pos.db', function (require) {
    "use strict";
    var pos_db = require('point_of_sale.DB');

    pos_db.include({
        _partner_search_string: function (partner) {
            var str = this._super(partner);
            str = str.replace('\n', '');
            if (partner.vat) {
                str += '|' + partner.vat;
            }
             return str + '\n';
        }
    });
});