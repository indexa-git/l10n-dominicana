odoo.define('ncf_pos.models', function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var rpc = require('web.rpc');

    models.load_fields('res.partner', ['sale_fiscal_type']);
    models.load_fields('pos.config', ['default_partner_id', 'print_pdf', 'ncf_control']);
    models.load_fields('res.company', ['street', 'street2', 'city', 'state_id', 'country_id', 'zip']);
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
            self.db.pos_all_orders = order || [];
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
            self.db.pos_all_order_lines = order_lines || [];
            self.db.line_by_id = {};
            order_lines.forEach(function (line) {
                self.db.line_by_id[line.id] = line;
            });
        }
    }], {
        'after': 'product.product'
    });
    models.load_models([{
        label: "Custom Account Journal",
        loaded: function (self, tmp) {
            var cashregister_credit_note = $.extend({}, self.cashregisters[0]);

            for (var n in self.cashregisters) {
                if (self.cashregisters[n].journal.type.toLowerCase() == "cash") {
                    cashregister_credit_note = $.extend({}, self.cashregisters[n]);
                    break;
                }
            }
            cashregister_credit_note = $.extend(cashregister_credit_note, {
                id: 10001,
                journal_id: [10001, 'Nota de Credito'],
                journal: {type: 'cash', id: 10001, sequence: 10001},
                css_class: 'altlight',
                show_popup: true,
                popup_name: 'textinput',
                popup_options: {}
            });

            //Creamos una forma de pago especial para la Nota de Credito
            self.cashregisters.push(cashregister_credit_note);
            self.cashregisters_by_id[cashregister_credit_note.id] = cashregister_credit_note;
        }
    }], {
        'after': 'account.journal'
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.invoices = [];

            this.sale_fiscal_type_selection = []; // this object define sale_fiscal_type on pos
            this.sale_fiscal_type_vat = []; // this object define relation between sale_fiscal_type and vat on pos
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
                    self.sale_fiscal_type_selection = result.sale_fiscal_type;
                    self.sale_fiscal_type_vat = result.sale_fiscal_type_vat;
                });
        },

        /**
         * Devuelve el label del tipo fiscal del cliente
         * @param {string} sale_fiscal_type - Tipo fiscal del cliente
         * @return {string}
         */
        get_sale_fiscal_type_label: function (sale_fiscal_type) {
            var label = _.find(this.sale_fiscal_type_selection, function (item) {
                return item[0] === sale_fiscal_type;
            });
            return label[1];
        },

        /**
         * Devuelve el label del tipo fiscal del cliente
         * @param {string} sale_fiscal_type - Tipo fiscal del cliente
         * @return {string}
         */
        get_sale_fiscal_type_label: function (sale_fiscal_type) {
            var label = _.find(this.sale_fiscal_type_selection, function (item) {
                return item[0] === sale_fiscal_type;
            });

            if (label[0] == 'fiscal' || label[0] == 'gov' || label[0] == 'special'){
                label[1] = 'Crédito';
            }
            if (label[0] == 'final' || label[0] == 'unico'){
                label[1] = 'Consumo';
            }
            return label[1];
        },

        /**
         * Get the next ncf sequence
         */
        get_next_ncf: function (sale_fiscal_type, invoice_journal_id, is_return_order) {
            var self = this;
            var order = self.get_order();
            var args = [
                sale_fiscal_type,
                invoice_journal_id,
                is_return_order
            ];

            var ncfPromise = rpc.query({
                model: 'pos.order',
                method: 'get_next_ncf',
                args: args,
            }, {
                timeout: 30000,
                shadow: ""
            }).then(function (next_ncf) {
                order.ncf = next_ncf;
                console.info("Order NCF validated: " + next_ncf);
            }).fail(function (type, error){
                console.error('The following error has been ocurred', error);
            });
            return ncfPromise;
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

            if (order) {
                var order_id = this.db.add_order(order.export_as_JSON());
            }

            this.flush_mutex.exec(function () {
                var done = new $.Deferred(); // holds the mutex
                // send the order to the server
                // we have a 30 seconds timeout on this push.
                // FIXME: if the server takes more than 30 seconds to accept the order,
                // the client will believe it wasn't successfully sent, and very bad
                // things will happen as a duplicate will be sent next time
                // so we must make sure the server detects and ignores duplicated orders
                var transfer = self._flush_orders(self.db.get_orders(), {
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
        getDatetime: function () {
            var date = new Date(),
                time = new Date(),
                timezone = 'es-ES',
                dateOptions = {day: '2-digit', month: '2-digit', year: 'numeric'},
                timeOptions = {hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true};

            return {
                date: date.toLocaleDateString(timezone, dateOptions),
                time: time.toLocaleTimeString(timezone, timeOptions),
                datetime: date.toLocaleDateString(timezone, _.extend(dateOptions, timeOptions))
            }
        },
        set_order: function (order) {
            _super_posmodel.set_order.call(this, order);

            if (order && order.is_return_order === true)
                this.gui.show_screen('payment');
        },
        /**
         * Envia un arreglo con las ordenes al servidor para generar las facturas
         * y luego de creadas facturas para las que sean de nota de credito actualizamos
         * la BD offline con los cambios
         * @param {object} orders - Objeto con la lista de ordenes
         * @param {object} options - Objeto con los configuracion opcional
         * @returns {*} Deferred con la lista de ids generados en el servidor
         * @private
         */
        _save_to_server: function (orders, options) {
            var self = this;
            return _super_posmodel._save_to_server.call(this, orders, options).always(function () {
                _.each(orders || [], function (order) {
                    order = order.data;
                    if (order.is_return_order === true) {
                        order.lines.forEach(function (line) {
                            var original_line = self.db.line_by_id[line[2].original_line_id];

                            if (original_line)
                                original_line.line_qty_returned += Math.abs(line[2].qty);
                        });
                    }
                });
            });
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            this.return_status = '-';
            this.is_return_order = false;
            this.return_order_id = false;
            this.orderlineList = [];
            this.ncf = false;
            _super_order.initialize.call(this, attributes, options);

            this.ncf_control = this.pos.config.ncf_control;

            if (this.pos.config.iface_invoicing) {
                var pos_default_partner = this.pos.config.default_partner_id;

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
            this.to_invoice = json.to_invoice;
            this.ncf = json.ncf;
            this.ncf_control = json.ncf_control;
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
                amount_total: parseFloat(json.amount_total || 0),
                to_invoice: this.to_invoice,
                ncf: this.ncf,
                ncf_control: this.ncf_control
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

    var super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function (attr, options) {
            this.credit_note_id = null;
            this.note = ''
            super_paymentline.initialize.call(this, attr, options);
        },
        init_from_JSON: function (json) {
            super_paymentline.init_from_JSON.call(this, json);
            this.credit_note_id = json.credit_note_id;
            this.note = json.note;
        },
        export_as_JSON: function () {
            var json = super_paymentline.export_as_JSON.call(this);

            $.extend(json, {
                credit_note_id: this.credit_note_id,
                note: this.note
            });
            return json;
        }
    });
});
