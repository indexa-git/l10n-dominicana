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
