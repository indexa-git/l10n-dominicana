// © 2018 Jefferson Benzan <jbenzan@gruponeotec.com>
// © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
// © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>

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

odoo.define('ncf_pos.invoices', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');

    var QueryInvoicesButton = screens.ActionButtonWidget.extend({
        template: 'QueryInvoicesButton',
        button_click: function () {
            this.pos.get_orders_from_server();
            this.gui.show_screen('invoiceslist');
        }
    });

    screens.define_action_button({
        'name': 'invoices_query',
        'widget': QueryInvoicesButton,
        'condition': function () {
            return true;
        }
    });
});
