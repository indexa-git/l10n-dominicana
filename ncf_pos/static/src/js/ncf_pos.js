odoo.define('ncf_pos.ncf_ticket', function (require) {
    "use strict";

    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var Model = require('web.DataModel');

    var QWeb = core.qweb;

    screens.ReceiptScreenWidget.include({

        ncf_render_receipt: function (fiscal_data) {
            var order = this.pos.get_order();
            order.fiscal_type_name = fiscal_data.fiscal_type_name;
            order.ncf = fiscal_data.ncf;
            order.origin_ncf = fiscal_data.origin;
            this.$('.pos-receipt-container').html(QWeb.render('PosTicket', {
                widget: this,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
            }));
        },
        render_receipt: function () {
            var self = this;
            var order = this.pos.get_order();
            $(".pos-sale-ticket").hide();
            $(".button.next.highlight").hide();
            $(".button.print").hide();
            
            new Model('pos.order').call("get_fiscal_data", [order.name]).then(function (fiscal_data) {
                self.ncf_render_receipt(fiscal_data);
                $(".pos-sale-ticket").show();
                $(".button.next.highlight").show();
                $(".button.print").show();
            });
        }
    });

});
