odoo.define('ncf_pos.models', function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var rpc = require('web.rpc');

    models.load_fields("res.partner", ['sale_fiscal_type']);
    models.load_fields("pos.config", ['pos_default_partner_id']);

    models.load_models([{
        model: 'pos.order',
        fields: ['id', 'name', 'date_order', 'partner_id', 'lines', 'pos_reference', 'invoice_id'],
        domain: function (self) {
            var domain_list = [];
            if (self.config.order_loading_options == 'n_days') {
                var today = new Date();
                var validation_date = new Date(today.setDate(today.getDate() - self.config.number_of_days)).toISOString();
                domain_list = [
                    ['date_order', '>', validation_date],
                    ['state', 'not in', ['draft', 'cancel']]
                ];
            } else
                domain_list = [
                    ['session_id', '=', self.pos_session.name],
                    ['state', 'not in', ['draft', 'cancel']]
                ];
            return domain_list;
        },
        loaded: function (self, wk_order) {
            self.db.pos_all_orders = wk_order;
            self.db.order_by_id = {};
            wk_order.forEach(function (order) {
                var order_date = new Date(order.date_order);
                var utc = order_date.getTime() - (order_date.getTimezoneOffset() * 60000);
                order.date_order = new Date(utc).toLocaleString();
                self.db.order_by_id[order.id] = order;
            });
        }
    }, {
        model: 'pos.order.line',
        fields: ['product_id', 'order_id', 'qty', 'discount', 'price_unit', 'price_tax', 'price_subtotal_incl', 'price_subtotal'],
        domain: function (self) {
            var order_lines = [];
            var orders = self.db.pos_all_orders;
            for (var i = 0; i < orders.length; i++) {
                order_lines = order_lines.concat(orders[i].lines);
            }
            return [
                ['id', 'in', order_lines]
            ];
        },
        loaded: function (self, wk_order_lines) {
            self.db.pos_all_order_lines = wk_order_lines;
            self.db.line_by_id = {};
            wk_order_lines.forEach(function (line) {
                self.db.line_by_id[line.id] = line;
            });
        }
    }], {
        'after': 'product.product'
    });


    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var self = this;
            this.invoices = [];

            // This object define sale_fiscal_type con pos
            this.sale_fiscal_type_selection = [];
            _super_posmodel.initialize.call(this, session, attributes);
        },

        load_server_data: function () {
            this.get_sale_fiscal_type_selection();

            return _super_posmodel.load_server_data.call(this);
        },

        get_sale_fiscal_type_selection: function () {
            var self = this;

            rpc.query({
                model: 'res.partner',
                method: 'get_sale_fiscal_type_selection',
                args: []
            }, {})
                .then(function (result) {
                    self.sale_fiscal_type_selection = result;
                });
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.apply(this, arguments);

            if (this.pos.config.iface_invoicing) {
                var pos_default_partner = this.pos.config.pos_default_partner_id;
                this.to_invoice = true;

                if (pos_default_partner) {
                    var client = this.pos.db.get_partner_by_id(pos_default_partner[0]);

                    if (client)
                        this.set_client(client);
                }
            }
        }
    });
});