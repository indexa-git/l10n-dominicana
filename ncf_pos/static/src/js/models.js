odoo.define('ncf_pos.models', function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var rpc = require('web.rpc');

    models.load_fields('res.partner', ['sale_fiscal_type']);
    models.load_fields('pos.config', ['pos_default_partner_id', 'print_pdf']);
    models.load_fields('product.product', 'not_returnable');

    models.load_models([{
        model: 'pos.order',
        fields: ['id', 'name', 'date_order', 'partner_id', 'lines', 'pos_reference', 'invoice_id',
            'amount_total', 'number', 'statement_ids', 'return_order_id', 'is_return_order',
            'return_status'],
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
            domain_list.push(['is_return_order', '=', false]);
            return domain_list;
        },
        loaded: function (self, order) {
            self.db.pos_all_orders = order;
            self.db.order_by_id = {};
            order.forEach(function (order) {
                var order_date = new Date(order.date_order);
                var utc = order_date.getTime() - (order_date.getTimezoneOffset() * 60000);

                order.date_order = new Date(utc).toLocaleString();
                self.db.order_by_id[order.id] = order;
            });
        }
    }, {
        model: 'account.invoice',
        fields: ['number'],
        domain: function (self) {
            var invoice_ids = self.db.pos_all_orders.map(function (order) {
                return order.invoice_id[0];
            });

            return [['id', 'in', invoice_ids]];
        },
        loaded: function (self, invoices) {
            var invoice_by_id = {};

            invoices.forEach(function (invoice) {
                invoice_by_id[invoice.id] = invoice;
            });

            self.db.pos_all_orders.forEach(function (order, ix) {
                var invoice_id = invoice_by_id[order.invoice_id[0]];
                var number = invoice_id && invoice_id.number;

                self.db.pos_all_orders[ix].number = number;
                self.db.order_by_id[order.id].number = number;
            });
        }
    }, {
        model: 'pos.order.line',
        fields: ['product_id', 'order_id', 'qty', 'discount', 'price_unit', 'price_tax', 'price_subtotal_incl',
            'price_subtotal', 'line_qty_returned'],
        domain: function (self) {
            var orders = self.db.pos_all_orders;
            var order_lines = [];

            for (var i in orders)
                order_lines = order_lines.concat(orders[i].lines);

            return [
                ['id', 'in', order_lines]
            ];
        },
        loaded: function (self, order_lines) {
            self.db.pos_all_order_lines = order_lines;
            self.db.line_by_id = {};
            order_lines.forEach(function (line) {
                self.db.line_by_id[line.id] = line;
            });
        }
    }], {
        'after': 'product.product'
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.invoices = [];

            // This object define sale_fiscal_type on pos
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
        },
        // saves the order locally and try to send it to the backend and make an invoice
        // returns a deferred that succeeds when the order has been posted and successfully generated
        // an invoice. This method can fail in various ways:
        // error-no-client: the order must have an associated partner_id. You can retry to make an invoice once
        //     this error is solved
        // error-transfer: there was a connection error during the transfer. You can retry to make the invoice once
        //     the network connection is up
        push_and_invoice_order: function (order) {
            var self = this;
            var invoiced = new $.Deferred();

            if (!order.get_client()) {
                invoiced.reject({code: 400, message: 'Missing Customer', data: {}});
                return invoiced;
            }

            var order_id = this.db.add_order(order.export_as_JSON());

            this.flush_mutex.exec(function () {
                var done = new $.Deferred(); // holds the mutex
                // send the order to the server
                // we have a 30 seconds timeout on this push.
                // FIXME: if the server takes more than 30 seconds to accept the order,
                // the client will believe it wasn't successfully sent, and very bad
                // things will happen as a duplicate will be sent next time
                // so we must make sure the server detects and ignores duplicated orders
                var transfer = self._flush_orders([self.db.get_order(order_id)], {
                    timeout: 30000,
                    to_invoice: true
                });

                transfer.fail(function (error) {
                    invoiced.reject(error);
                    done.reject();
                });
                if (self.config.print_pdf) {
                    // on success, get the order id generated by the server
                    transfer.pipe(function (order_server_id) {

                        // generate the pdf and download it
                        self.chrome.do_action('point_of_sale.pos_invoice_report', {
                            additional_context: {
                                active_ids: order_server_id,
                            }
                        }).done(function () {
                            invoiced.resolve();
                            done.resolve();
                        });
                    });
                } else {
                    invoiced.resolve();
                    done.resolve();
                }
                return done;
            });
            return invoiced;
        },
        set_order: function (order) {
            _super_posmodel.set_order.call(this, order);

            if (order && order.is_return_order === true)
                this.gui.show_screen('payment');
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.return_status = '-';
            this.is_return_order = false;
            this.return_order_id = false;
            this.orderlineList = [];
            _super_order.initialize.call(this, attributes, options);
            if (this.pos.config.iface_invoicing) {
                var pos_default_partner = this.pos.config.pos_default_partner_id;

                this.to_invoice = true;
                if (pos_default_partner) {
                    var client = this.pos.db.get_partner_by_id(pos_default_partner[0]);

                    if (client)
                        this.set_client(client);
                }
            }
        },
        init_from_JSON: function (json) {
            var self = this;

            _super_order.init_from_JSON.call(this, json);
            this.return_status = json.return_status;
            this.is_return_order = json.is_return_order;
            this.return_order_id = json.return_order_id;
            this.amount_total = json.amount_total;
            if (this.orderlines && $.isArray(this.orderlines.models)) {
                this.orderlines.models.forEach(function (line) {
                    var productDefCode = line.product.default_code;

                    self.orderlineList.push(
                        {
                            line_id: line.id,
                            product_id: line.product.id,
                            product_name: (productDefCode && '[' + productDefCode + '] ' || '') + line.product.display_name,
                            quantity: line.quantity,
                            price: line.price
                        });
                });
            }
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.call(this);

            $.extend(json, {
                return_status: this.return_status,
                is_return_order: this.is_return_order,
                return_order_id: this.return_order_id,
                amount_total: parseFloat(json.amount_total || 0)
            });
            return json;
        }
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.line_qty_returned = 0;
            this.original_line_id = null;
            _super_orderline.initialize.call(this, attr, options);
        },
        init_from_JSON: function (json) {
            _super_orderline.init_from_JSON.call(this, json);
            this.line_qty_returned = json.line_qty_returned;
            this.original_line_id = json.original_line_id;
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.call(this);

            $.extend(json, {
                line_qty_returned: this.line_qty_returned,
                original_line_id: this.original_line_id
            });
            return json;
        }
    });
});
