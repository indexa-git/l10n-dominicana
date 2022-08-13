// © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
// © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
// © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
// © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
// © 2019-2020 Raul  Ovalle <raulovallet@gmail.com>

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

odoo.define('l10n_do_pos.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var _t = core._t;
    var _super_order = models.Order.prototype;
    var _super_posmodel = models.PosModel.prototype;
    var rpc = require('web.rpc');

    models.load_fields('res.partner', ['l10n_do_dgii_tax_payer_type']);
    models.load_fields('pos.config', ['l10n_do_default_partner_id']);

    models.load_fields('account.journal', [
        'l10n_latam_use_documents',
        'l10n_do_sequence_ids',
        'l10n_do_payment_form',
    ]);

    models.load_models({
        model: 'account.journal',
        fields: ['name', 'l10n_latam_use_documents', 'l10n_do_sequence_ids'],
        domain: function (self) {
            return [['id', '=', self.config.invoice_journal_id[0]]];
        },
        loaded: function (self, journals) {
            self.invoice_journal = false;
            if (journals[0]) {
                self.invoice_journal = journals[0];
            }
        },
    });

    //TODO: CHECK THIS
    models.load_models([{
        model: 'pos.order',
        fields: ['id', 'name', 'date_order', 'partner_id', 'lines', 'pos_reference', 'account_move', 'amount_total',
            'l10n_latam_document_number', 'payment_ids', 'l10n_do_return_order_id', 'l10n_do_is_return_order', 'l10n_do_return_status'],
        domain: function (self) {
            var domain_list = [];

            if (self.config.l10n_do_order_loading_options === 'n_days') {
                var today = new Date();
                var validation_date = new Date(today);
                validation_date.setDate(today.getDate() - self.config.l10n_do_number_of_days);

                domain_list = [
                    ['account_move.invoice_date', '>', validation_date.toISOString()],
                    ['state', 'not in', ['draft', 'cancel']],
                    ['config_id', '=', self.config.id],
                ];
            } else {
                domain_list = [
                    ['session_id', '=', self.pos_session.id],
                    ['state', 'not in', ['draft', 'cancel']],
                ];
            }
            domain_list.push(['l10n_do_is_return_order', '=', false]);
            return domain_list;
        },
        loaded: function (self, orders) {
            self.db.pos_all_orders = orders || [];
            self.db.order_by_id = {};
            orders.forEach(function (order) {
                order.number = order.ncf;
                order.account_move = [order.account_move[0], order.ncf];
                self.db.order_by_id[order.id] = order;
            });
        },
    }, {
        model: 'account.move',
        fields: ['l10n_latam_document_number'],
        domain: function (self) {
            var invoice_ids = self.db.pos_all_orders.map(function (order) {
                return order.account_move[0];
            });

            return [['id', 'in', invoice_ids]];
        },
        loaded: function (self, invoices) {
            var invoice_by_id = {};

            invoices.forEach(function (invoice) {
                invoice_by_id[invoice.id] = invoice;
            });
            self.db.pos_all_orders.forEach(function (order, ix) {
                var invoice_id = invoice_by_id[order.account_move[0]];
                var l10n_latam_document_number = invoice_id && invoice_id.l10n_latam_document_number;
                self.db.pos_all_orders[ix].l10n_latam_document_number = l10n_latam_document_number;
                self.db.order_by_id[order.id].l10n_latam_document_number = l10n_latam_document_number;
            });
        },
    }, {
        model: 'account.move',
        fields: ['l10n_latam_document_number', 'partner_id'],
        // TODO: CHECK WTF IS residual
        domain: function (self) {
            var today = new Date();
            var validation_date = new Date(today);
            validation_date.setDate(today.getDate() - self.config.l10n_do_credit_notes_number_of_days);
            //TODO: try analize correct date
            return [
                ['type', '=', 'out_refund'], ['state', '!=', 'paid'],
                ['invoice_date', '>', validation_date.toISOString()],
            ];
        },
        loaded: function (self, invoices) {
            var credit_note_by_id = {};
            var credit_notes_by_partner_id = {};
            var partner_id = false;

            _.each(invoices, function (invoice) {
                partner_id = invoice.partner_id[0];
                invoice.partner_id = self.db.get_partner_by_id(partner_id);
                credit_note_by_id[invoice.id] = invoice;
                credit_notes_by_partner_id[partner_id] = credit_notes_by_partner_id[partner_id] || [];
                credit_notes_by_partner_id[partner_id].push(invoice);
            });

            self.db.credit_note_by_id = credit_note_by_id;
            self.db.credit_notes_by_partner_id = credit_notes_by_partner_id;
        },
    }, {
        model: 'pos.order.line',
        fields: ['product_id', 'order_id', 'qty', 'discount', 'price_unit', 'price_subtotal_incl',
            'price_subtotal', 'l10n_do_line_qty_returned'],
        domain: function (self) {
            var orders = self.db.pos_all_orders;
            var order_lines = [];

            for (var i in orders) {
                order_lines = order_lines.concat(orders[i].lines);
            }

            return [
                ['id', 'in', order_lines],
            ];
        },
        loaded: function (self, order_lines) {
            self.db.pos_all_order_lines = order_lines || [];
            self.db.line_by_id = {};
            order_lines.forEach(function (line) {
                self.db.line_by_id[line.id] = line;
            });
        },
    }], {
        'after': 'product.product',
    });

    models.load_models([{
        label: "Custom Account Journal",
        loaded: function (self, tmp) {
            var payment_method_credit_note = $.extend({}, self.payment_methods[0]);
            for (var n in self.payment_methods) {
                if (self.payment_methods[n].is_cash_count) {
                    payment_method_credit_note = $.extend({}, self.payment_methods[n]);
                    break;
                }
            }
            payment_method_credit_note = $.extend(payment_method_credit_note, {
                id: 10001,
                css_class: 'altlight',
                show_popup: true,
                popup_name: 'textinput',
                popup_options: {},
                name: 'Nota de Credito',
            });

            // Creamos una forma de pago especial para la Nota de Credito
            self.payment_methods.push(payment_method_credit_note);
            self.payment_methods_by_id[payment_method_credit_note.id] = payment_method_credit_note;
        },
    }], {
        'after': 'pos.payment.method',
    });

    models.load_models({
        model: 'ir.sequence',
        fields: [
            'l10n_latam_document_type_id',
        ],
        domain: function (self) {
            return [
                ['id', 'in', self.invoice_journal.l10n_do_sequence_ids],
            ];
        },
        loaded: function (self, latam_sequences) {
            self.l10n_latam_sequences = latam_sequences;
            console.log('Sequences loaded:', latam_sequences);
        },
    });

    models.load_models({
        model: 'l10n_latam.document.type',
        fields: [
            'name',
            'code',
            'l10n_do_ncf_type',
            'is_vat_required',
            'internal_type',
            'doc_code_prefix',
            'country_id',
        ],
        domain: function () {
            return [
                ['internal_type', 'in', ['invoice', 'credit_note']],
                ['active', '=', true],
                ['code', '=', 'B'],
            ];
        },
        loaded: function (self, latam_document_types) {
            latam_document_types.forEach(function (latam_document_type, index, array) {
                if (latam_document_type.internal_type === 'credit_note') {
                    self.l10n_latam_document_type_credit_note = latam_document_type;
                }
            });
            self.l10n_latam_document_types = latam_document_types.filter(
                item => item.id !== self.l10n_latam_document_type_credit_note.id);
            console.log('Document types loaded:', latam_document_types);
        },
    });

    models.Order = models.Order.extend({
        initialize: function () {
            _super_order.initialize.apply(this, arguments);
            var self = this;
            this.l10n_latam_sequence_id = false;
            this.l10n_latam_document_type_id = false;
            this.l10n_latam_document_type =
                self.pos.get_latam_document_type_by_prefix();
            this.to_invoice_backend = false;

            this.l10n_do_return_status = '-';
            this.l10n_do_origin_ncf = '';
            this.l10n_do_is_return_order = false;
            this.l10n_do_return_order_id = false;
            this.set_to_invoice(true);
            this.save_to_db();
        },

        set_latam_document_type: function (l10n_latam_document_type) {
            this.l10n_latam_document_type = l10n_latam_document_type;
            this.l10n_latam_document_type_id = l10n_latam_document_type.id;
            this.save_to_db();
            this.latam_document_type_changed();
        },

        get_latam_document_type: function () {
            return this.l10n_latam_document_type;
        },

        latam_document_type_changed: function () {
            var current_order = this.pos.get_order();
            if (current_order){
                var latam_document_type_name =
                    current_order.l10n_latam_document_type.name || false;
                this.pos.gui.screen_instances.payment
                    .$('.js_latam_document_type_name').text(
                        latam_document_type_name);
                this.pos.gui.screen_instances.products
                    .$('.js_latam_document_type_name').text(
                    latam_document_type_name);
            }
        },
        // TODO: check this is meaby its important
        // init_from_JSON: function (json) {
        //     var self = this;
        //     _super_order.init_from_JSON.call(this, json);
        //     this.l10n_do_return_status = json.l10n_do_return_status;
        //     this.l10n_do_is_return_order = json.l10n_do_is_return_order;
        //     this.l10n_do_return_order_id = json.l10n_do_return_order_id;
        //     this.amount_total = json.amount_total;
        //     this.to_invoice = json.to_invoice;
        //     this.ncf = json.ncf;
        //     this.ncf_control = json.ncf_control;
        //     if (this.orderlines && $.isArray(this.orderlines.models)) {
        //         this.orderlines.models.forEach(function (line) {
        //             var productDefCode = line.product.default_code;
        //             self.orderlineList.push(
        //                 {
        //                     line_id: line.id,
        //                     product_id: line.product.id,
        //                     product_name: (productDefCode && '[' + productDefCode + '] ' || '') + line.product.display_name,
        //                     quantity: line.quantity,
        //                     price: line.price,
        //                 });
        //         });
        //     }
        // },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.call(this, json);
            this.l10n_latam_document_number = json.l10n_latam_document_number;
            this.l10n_do_ncf_expiration_date = json.l10n_do_ncf_expiration_date
            this.l10n_latam_sequence_id = json.l10n_latam_sequence_id;
            this.l10n_latam_document_type_id = json.l10n_latam_document_type_id;
            this.to_invoice_backend = json.to_invoice_backend;
            this.l10n_do_return_status = json.l10n_do_return_status;
            this.l10n_do_origin_ncf = json.l10n_do_origin_ncf;
            this.l10n_do_is_return_order = json.l10n_do_is_return_order;
            this.l10n_do_return_order_id = json.l10n_do_return_order_id;
            this.set_latam_document_type(
                this.pos.get_latam_document_type_by_id(
                    json.l10n_latam_document_type_id));
        },
        export_as_JSON: function () {

            var self = this;
            var loaded = _super_order.export_as_JSON.call(this);
            var current_order = self.pos.get_order();

            if (current_order) {
                loaded.l10n_latam_document_number =
                    current_order.l10n_latam_document_number;
                loaded.l10n_do_ncf_expiration_date = current_order.l10n_do_ncf_expiration_date;
                loaded.l10n_latam_sequence_id =
                    current_order.l10n_latam_sequence_id;
                loaded.l10n_latam_document_type_id =
                    current_order.l10n_latam_document_type_id;
                loaded.to_invoice_backend = current_order.to_invoice_backend;

                loaded.l10n_do_return_status = current_order.l10n_do_return_status;
                loaded.l10n_do_origin_ncf = current_order.l10n_do_origin_ncf;
                loaded.l10n_do_is_return_order = current_order.l10n_do_is_return_order;
                loaded.l10n_do_return_order_id = current_order.l10n_do_return_order_id;
            }

            return loaded;
        },
        set_to_invoice: function (to_invoice) {
            _super_order.set_to_invoice.call(this, to_invoice);
            this.to_invoice_backend = to_invoice;
        },

        set_client: function(client) {
            var self = this;
            _super_order.set_client.apply(this, arguments);
            if (client){
                self.set_latam_document_type(
                    self.pos.get_latam_document_type_by_l10n_do_ncf_type(
                        self.pos.ncf_types_data.issued[client.l10n_do_dgii_tax_payer_type][0])
                );
            }else{
                self.set_latam_document_type(
                    self.pos.get_latam_document_type_by_l10n_do_ncf_type()
                );
            }
        },

    });

    var super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function (attr, options) {
            this.credit_note_id = null;
            this.note = '';
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
                note: this.note,
                payment_reference: this.payment_method.payment_reference,
            });
            return json;
        },
    });

    //TODO: CHECK AVOVE THIS PART

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.l10n_do_line_qty_returned = 0;
            this.l10n_do_original_line_id = null;
            _super_orderline.initialize.call(this, attr, options);
        },
        init_from_JSON: function (json) {
            _super_orderline.init_from_JSON.call(this, json);
            this.l10n_do_line_qty_returned = json.l10n_do_line_qty_returned;
            this.l10n_do_original_line_id = json.l10n_do_original_line_id;
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.call(this);

            $.extend(json, {
                l10n_do_line_qty_returned: this.l10n_do_line_qty_returned,
                l10n_do_original_line_id: this.l10n_do_original_line_id,
            });
            return json;
        },
    });


    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.invoices = [];
            this.sale_fiscal_type_selection = []; // This list define sale_fiscal_type on pos
            this.sale_fiscal_type_default_id = 'final'; // This define the default id of sale_fiscal_type
            this.sale_fiscal_type = []; // This list define sale_fiscal_type on pos
            this.sale_fiscal_type_by_id = {}; // This object define sale_fiscal_type on pos
            this.sale_fiscal_type_vat = []; // This list define relation between sale_fiscal_type and vat on pos
            this.tax_payer_type_list = [];
            this.ncf_types_data = {};

            _super_posmodel.initialize.call(this, session, attributes);
        },
        get_latam_document_type_by_id: function (id) {
            var self = this;
            var res_latam_document_type = false;
            // TODO: try make at best performance
            self.l10n_latam_document_types.forEach(
                function (latam_document_type) {
                    if (latam_document_type.id === id) {
                        res_latam_document_type = latam_document_type;
                    }
                });
            if (!res_latam_document_type) {
                res_latam_document_type =
                    this.get_latam_document_type_by_prefix();
            }
            return res_latam_document_type;
        },

        get_l10n_latam_sequence_by_document_type_id:
            function (document_type_id) {
                var result = false;
                var self = this;
                self.l10n_latam_sequences.forEach(
                    function (latam_sequence) {
                        if (latam_sequence.l10n_latam_document_type_id[0] ===
                            document_type_id) {
                            result = latam_sequence;
                        }
                    });
                return result;
            },

        get_latam_document_type_by_l10n_do_ncf_type: function (l10n_do_ncf_type) {
            var self = this;
            var res_latam_document_type = false;
            // TODO: try make at best performance
            if (!l10n_do_ncf_type) {
                l10n_do_ncf_type = 'consumer';
            }
            self.l10n_latam_document_types.forEach(
                function (latam_document_type) {
                    if (latam_document_type.l10n_do_ncf_type === l10n_do_ncf_type) {
                        res_latam_document_type = latam_document_type;
                    }
                });
            if (res_latam_document_type) {
                return res_latam_document_type;
            }
            self.gui.show_popup('error', {
                'title': _t('Fiscal document type not found'),
                'body': _t('This fiscal document type not exist.'),
            });
            return false;
        },

        get_latam_document_type_by_prefix: function (prefix) {
            var self = this;
            var res_latam_document_type = false;
            // TODO: try make at best performance
            var real_prefix = prefix;
            if (!real_prefix) {
                real_prefix = 'B02';
            }
            self.l10n_latam_document_types.forEach(
                function (latam_document_type) {
                    if (latam_document_type.doc_code_prefix === real_prefix) {
                        res_latam_document_type = latam_document_type;
                    }
                });
            if (res_latam_document_type) {
                return res_latam_document_type;
            }
            self.gui.show_popup('error', {
                'title': _t('Fiscal document type not found'),
                'body': _t('This fiscal document type not exist.'),
            });
            return false;
        },

        loading_screen_on: function () {
            $('.freeze_screen_spinner').addClass("active_state");
        },

        loading_screen_off: function () {
            $('.freeze_screen_spinner').removeClass("active_state");
        },


        // TODO: check this part for credit order
        set_order: function (order) {
            _super_posmodel.set_order.call(this, order);

            if (order && order.l10n_do_is_return_order === true) {
                this.gui.show_screen('payment');
            }
        },

        get_orders_from_server: function () {
            var self = this;
            var kwargs = {};
            var loading_type = posmodel.config.l10n_do_order_loading_options;
            if (loading_type === 'n_days') {
                kwargs.day_limit = this.config.l10n_do_number_of_days || 0;
                kwargs.config_id = this.config.id;
            } else if (loading_type === "current_session") {
                kwargs.session_id = posmodel.pos_session.id;
            }
            rpc.query({
                model: 'pos.order',
                method: 'order_search_from_ui',
                args: [],
                kwargs: kwargs,
            }, {})
                .then(function (result) {
                    var orders = result && result.orders || [];
                    var orderlines = result && result.orderlines || [];

                    orders.forEach(function (order) {
                        var obj = self.db.order_by_id[order.id];

                        if (!obj) {
                            self.db.pos_all_orders.unshift(order);
                        }
                        self.db.order_by_id[order.id] = order;
                    });
                    self.db.pos_all_order_lines.concat(orderlines);
                    orderlines.forEach(function (line) {
                        self.db.line_by_id[line.id] = line;
                    });

                    self.gui.screen_instances.invoiceslist.render_list(
                        self.db.pos_all_orders);

                });
        },

        get_tax_payer_name: function (tax_payer_type_id) {
             var tax_payer_name = 'N/A';
             this.tax_payer_type_list.forEach(function (tax_payer_type) {
                 if(tax_payer_type[0] === tax_payer_type_id)
                     tax_payer_name = tax_payer_type[1];
             });
             return tax_payer_name
        },

        load_server_data: function () {
            var self = this;
            var loaded = _super_posmodel.load_server_data.call(this);
            return loaded.then(function() {
                return rpc.query({
                    model: "pos.config",
                    method: "get_l10n_do_fiscal_type_data",
                    args: [false],
                }).then(function(result) {
                    self.tax_payer_type_list = result.tax_payer_type_list;
                    self.ncf_types_data = result.ncf_types_data;
                });
            });
        },

    });

    return models;
});
