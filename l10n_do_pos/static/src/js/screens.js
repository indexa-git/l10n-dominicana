// © 2015-2018 Eneldo Serrata <eneldo@marcos.do>
// © 2017-2018 Gustavo Valverde <gustavo@iterativo.do>
// © 2018 Jorge Hernández <jhernandez@gruponeotec.com>
// © 2018 Francisco Peñaló <frankpenalo24@gmail.com>
// © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>
// © 2019-2020 Raul Ovalle <raulovallet@gmail.com>

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


odoo.define('l10n_do_pos.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var _t = core._t;

    var QueryInvoicesButton = screens.ActionButtonWidget.extend({
        template: 'QueryInvoicesButton',
        button_click: function () {
            this.pos.get_orders_from_server();
            this.gui.show_screen('invoiceslist');
        },
    });

    screens.define_action_button({
        'name': 'invoices_query',
        'widget': QueryInvoicesButton,
        'condition': function () {
            return true;
        },
    });

    screens.PaymentScreenWidget.include({
        init: function (parent, options) {
            var self = this,
                popup_options = {
                    popup_name: "textinput",
                    title: 'Digite el número de NCF de la Nota de Crédito',
                    disable_keyboard_handler: true,
                    input_name: 'ncf',
                    text_input_value: '',
                    confirm: function (input_value) {
                        // var selection_val = $('.pos .popup select.credit_notes').val();
                        // if (selection_val) {
                        //     var credit_note = self.pos.db.credit_note_by_id[selection_val]
                        //     input_value = credit_note.reference;
                        // }
                        var msg_error = "";
                        rpc.query({
                            model: 'pos.order',
                            method: 'credit_note_info_from_ui',
                            args: [input_value],
                        }, {})
                            .then(function (result) {
                                var residual = parseFloat(result.residual) || 0;
                                var client = self.pos.get_client();
                                if (!client){
                                    client = {
                                        id: self.pos.config.l10n_do_default_partner_id[0]
                                    }
                                }

                                if (result.id === false) {
                                    msg_error = _t("La nota de credito no existe.");
                                } else if (!client  || (client && client.id !== result.partner_id)){
                                    msg_error = _t("La Nota de Crédito Pertenece a Otro Cliente");
                                } else if (residual < 1) {
                                    msg_error = _t("El balance de la Nota de Credito es 0.");
                                } else {
                                    var order = self.pos.get_order();
                                    var payment_method = self.pos.payment_methods_by_id[10001];
                                    var paymentline = order.paymentlines.find(function (pl) {
                                        return pl.note === input_value;
                                    });

                                    if (paymentline) {
                                        msg_error = "Esta Nota de Credito ya esta aplicada a la Orden";
                                    } else {
                                        order.add_paymentline(payment_method);
                                        order.selected_paymentline.credit_note_id = result.id;
                                        order.selected_paymentline.note = input_value;
                                        order.selected_paymentline.set_amount(residual); // Add paymentline for residual
                                        self.reset_input();
                                        self.order_changes();
                                        self.render_paymentlines();
                                        return false;
                                    }
                                }
                                popup_options.text_input_value = input_value;
                                self.gui.show_popup('error', {
                                    title: _t("Search") + " Nota de Credito",
                                    body: msg_error,
                                    disable_keyboard_handler: true,
                                    cancel: function () {
                                        self.gui.show_popup('textinput', popup_options);
                                    },
                                });
                            });
                    },
                },
                credit_card_options = {
                    popup_name: 'textinput',
                    title: 'Digite el número de Referencia',
                    disable_keyboard_handler: true,
                    input_name: 'credit_card',
                    text_input_value: '',
                    confirm: function (input) {
                        var payment_method = this.options.payment_method;
                        payment_method.payment_reference = input;
                        self.pos.get_order().add_paymentline(payment_method);
                        self.reset_input();
                        self.render_paymentlines();
                    },
                };

            this._super(parent, options);
            this.orderValidationDate = null;

            for (var n in this.pos.payment_methods) {
                var current_payment_method = this.pos.payment_methods[n];

                if (current_payment_method.id === 10001) {
                    // Set the popup options for the payment method Credit Note
                    current_payment_method.popup_options = popup_options;
                }
                // TODO: CREDIT CARD OPTIONS
                // else if (current_payment_method.journal.payment_form === "card" && !current_payment_method.credit) {
                //     // Set the popup options for the payment method Credit/Debit Card
                //     current_payment_method.popup_options = credit_card_options;
                // }

            }
        },
        show: function () {
            var self = this;
            var order = this.pos.get_order();
            var paymentContents = this.$('.left-content, .right-content, .back, .next');
            var refundContents = this.$('.refund-confirm-content, .cancel, .confirm');

            this._super();
            if (order && order.l10n_do_is_return_order) {
                var refundConfirm = this.$('.refund-confirm-content');

                paymentContents.addClass('oe_hidden');
                refundContents.removeClass('oe_hidden');
                this.$('.top-content h1').html(_t('Refund Order'));
                refundConfirm.empty();
                refundConfirm.append(QWeb.render('OrderRefundConfirm', {widget: this, order: order}));
                if (order.paymentlines.length === 0) {
                    var payment_method = this.pos.payment_methods[0];

                    for (var n in this.pos.payment_methods) {
                        if (this.pos.payment_methods[n].is_cash_count) {
                            payment_method = this.pos.payment_methods[n];
                            break;
                        }
                    }
                    order.add_paymentline(payment_method);
                    order.selected_paymentline.set_amount(order.get_total_with_tax()); // Add paymentline for total+tax
                }
                this.order_changes();
                this.$('.button.confirm').click(function () {
                    self.gui.show_popup('confirm', {
                        title: _t('Create') + ' ' + _t('Refund Order'),
                        body: _t('Are you sure you want to create this refund order?'),
                        confirm: function () {
                            self.validate_order();
                        },
                    });
                    return false;
                }).addClass('highlight');
                this.$('.button.cancel').click(function () {
                    $('.order-selector .deleteorder-button').click();
                    return false;
                });
                this.$('.button-custom.edit').click(function () {
                    var original_order = self.pos.db.order_by_id[order.l10n_do_return_order_id];
                    var original_orderlines = [];
                    var return_product = {};

                    order.orderlineList.forEach(function (obj) {
                        return_product[obj.product_id] = obj.quantity;
                    });
                    self.gui.show_popup('refund_order_popup', {
                        disable_keyboard_handler: true,
                        order: original_order,
                        orderlines: original_orderlines,
                        is_partial_return: true,
                        mode: 'edit',
                        confirm: function () {
                            var paymentlines = order.get_paymentlines();

                            for (var n = paymentlines.length - 1; n >= 0; n--) {
                                order.paymentlines.remove(paymentlines[n]);
                            }
                        },
                    });
                    return false;
                });
            } else {
                paymentContents.removeClass('oe_hidden');
                refundContents.addClass('oe_hidden');
            }
            this.$('.button.js_invoice').remove();
            // Improving the keyboard handling method
            this.gui.__disable_keyboard_handler();
            this.gui.__enable_keyboard_handler();
        },
        click_paymentmethods: function (id) {
            // Validamos que la orden tenga saldo pendiente antes de agregar una nueva linea de pago
            if (this.pos.get_order().get_due() <= 0) {
                this.gui.show_popup('alert', {
                    title: _t("Payment"),
                    body: _t("This order has no pending balance."),
                    disable_keyboard_handler: true,
                });
            } else {
                for (var i = 0; i < this.pos.payment_methods.length; i++) {
                    var payment_method = this.pos.payment_methods[i];

                    // Evaluamos si es una forma de pago especial que abre un popup
                    if (payment_method.id === id && payment_method.popup_options) {
                        var popup_options = _.extend(_.clone(payment_method.popup_options), {payment_method: payment_method});
                        this.gui.show_popup(popup_options.popup_name || 'alert', popup_options);
                        return false;
                    }
                }
                this._super(id);
            }
        },
        payment_input: function (input) {
            var order = this.pos.get_order();

            // Evitamos que se pueda cambiar el monto de la Nota de Credito
            if (order.selected_paymentline && order.selected_paymentline.payment_method.id === 10001) {
                return false;
            }
            this._super(input);
        },

        // TODO: check above this part ^^^^^^^^^^

        keyboard_off: function () {
            // That one comes from BarcodeEvents
            $('body').keypress(this.keyboard_handler);
            // That one comes from the pos, but we prefer to cover
            // all the basis
            $('body').keydown(this.keyboard_keydown_handler);
        },
        keyboard_on: function () {
            $('body').off('keypress', this.keyboard_handler);
            $('body').off('keydown', this.keyboard_keydown_handler);
        },

        renderElement: function () {
            this._super();
            var self = this;
            this.$('.js_set_latam_document_type').click(function () {
                self.click_set_latam_document_type();
            });
        },

        open_vat_popup: function () {
            var self = this;
            var current_order = self.pos.get_order();

            self.keyboard_on();
            self.gui.show_popup('textinput', {
                'title': _t('You need to select a customer with RNC/Céd for' +
                    ' this fiscal type, place writes RNC/Céd'),
                'vat': '',
                confirm: function (vat) {
                    self.keyboard_off();
                    if (!(vat.length === 9 || vat.length === 11) ||
                        Number.isNaN(Number(vat))) {

                        self.gui.show_popup('error', {
                            'title': _t('This not RNC or Cédula'),
                            'body': _t('Please check if RNC or Cédula is' +
                                ' correct'),
                            cancel: function () {
                                self.open_vat_popup();
                            },
                        });

                    } else {
                        // TODO: in future try optimize search partners
                        // link get_partner_by_id
                        self.keyboard_off();
                        var partner = self.pos.partners.find(
                            function (partner_obj) {
                                return partner_obj.vat === vat;
                            }
                        );
                        if (partner) {
                            current_order.set_client(partner);
                        } else {
                            // TODO: in future create automatic partner
                            self.gui.show_screen('clientlist');
                        }
                    }

                },
                cancel: function () {
                    self.keyboard_off();
                    if (!current_order.get_client()) {
                        current_order.set_latam_document_type(
                            this.pos.get_latam_document_type_by_prefix()
                        );
                    }
                },
            });
        },

        click_set_latam_document_type: function () {
            var self = this;
            var current_order = self.pos.get_order();
            var client = self.pos.get_client();
            var ncf_types_data = self.pos.ncf_types_data.issued['non_payer'];
            if (client && client.l10n_do_dgii_tax_payer_type)
                ncf_types_data = self.pos.ncf_types_data.issued[client.l10n_do_dgii_tax_payer_type];

            var latam_document_type_list =
                _.map(self.pos.l10n_latam_document_types,
                    function (latam_document_type) {
                        if (latam_document_type.internal_type === 'invoice' &&
                            ncf_types_data.includes(latam_document_type.l10n_do_ncf_type)) {
                            return {
                                label: latam_document_type.name,
                                item: latam_document_type,
                            };
                        }
                        return false;
                    });

            self.gui.show_popup('selection', {
                title: _t('Select document type'),
                list: latam_document_type_list,
                confirm: function (latam_document_type) {
                    current_order.set_latam_document_type(latam_document_type);
                    if (latam_document_type.is_vat_required && !client) {
                        self.open_vat_popup();
                    }
                    if (latam_document_type.is_vat_required && client) {
                        if (!client.vat) {
                            self.open_vat_popup();
                        }
                    }
                },
                is_selected: function (latam_document_type) {
                    var order = self.pos.get_order();
                    return latam_document_type ===
                        order.l10n_latam_document_type;
                },
            });
        },

        order_is_valid: function (force_validation) {

            var self = this;
            var current_order = this.pos.get_order();
            var client = current_order.get_client();
            var total = current_order.get_total_with_tax();
            if (current_order.to_invoice_backend) {
                current_order.to_invoice = false;
                current_order.save_to_db();
            }

            if (total === 0) {
                this.gui.show_popup('error', {
                    'title': _t('Sale in'),
                    'body': _t('You cannot make sales in 0, please add a ' +
                        'product with value'),
                });
                return false;
            }

            if (self.pos.invoice_journal.l10n_latam_use_documents &&
                current_order.to_invoice_backend) {

                var latam_sequence =
                    self.pos.get_l10n_latam_sequence_by_document_type_id(
                        current_order.l10n_latam_document_type.id
                    );

                if (!latam_sequence) {
                    this.gui.show_popup('error', {
                        'title': _t('Not fiscal sequence'),
                        'body': _t('Please configure correct fiscal sequence in invoice journal'),
                    });
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    return false;
                }

                if (!self.pos.config.l10n_do_default_partner_id && !client) {
                    this.gui.show_popup('error', {
                        'title': _t('No customer'),
                        'body': _t('Please select a customer or set one as default in the point of sale settings'),
                    });
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    return false;
                }

                if (current_order.l10n_latam_document_type.is_vat_required &&
                    !client) {

                    this.gui.show_popup('error', {
                        'title': _t('Required document (RNC/Céd.)'),
                        'body': _t('For invoice fiscal type ' +
                            current_order.fiscal_type.name +
                            ' its necessary customer, please select customer'),
                    });
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    return false;

                }

                if (current_order.l10n_latam_document_type.is_vat_required &&
                    !client.vat) {

                    this.gui.show_popup('error', {
                        'title': _t('Required document (RNC/Céd.)'),
                        'body': _t('For invoice fiscal type ' +
                            current_order.l10n_latam_document_type.name +
                            ' it is necessary for the customer have ' +
                            'RNC or Céd.'),
                    });
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    return false;
                }

                if (total >= 250000.00 && (!client || !client.vat)) {
                    this.gui.show_popup('error', {
                        'title': _t('Sale greater than RD$ 250,000.00'),
                        'body': _t('For this sale it is necessary for the ' +
                            'customer have ID'),
                    });
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    return false;
                }

            }


            if (this._super(force_validation)) {
                return true;
            }

            if (current_order.to_invoice_backend) {
                current_order.to_invoice = true;
                current_order.save_to_db();
            }

            return false;

        },

        finalize_validation: function () {
            var self = this;
            var current_order = this.pos.get_order();
            var _super = this._super.bind(this);
            if (current_order.to_invoice_backend &&
                self.pos.invoice_journal.l10n_latam_use_documents &&
                !current_order.l10n_latam_document_number) {
                var latam_sequence =
                    self.pos.get_l10n_latam_sequence_by_document_type_id(
                        current_order.l10n_latam_document_type.id
                    );
                self.pos.loading_screen_on();
                rpc.query({
                    model: 'ir.sequence',
                    method: 'get_l10n_do_fiscal_info',
                    args: [latam_sequence.id],
                }).then(function (res) {
                    self.pos.loading_screen_off();
                    current_order.l10n_latam_document_number = res.ncf;
                    current_order.l10n_do_ncf_expiration_date = res.expiration_date;
                    current_order.l10n_latam_sequence_id = latam_sequence.id;
                    current_order.l10n_latam_document_type_id =
                        current_order.l10n_latam_document_type.id;
                    current_order.save_to_db();
                    console.log(res);
                    _super();
                }, function (err) {
                    self.pos.loading_screen_off();
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    console.log('err', err);
                    err.event.preventDefault();
                    var error_body =
                        _t('Your Internet connection is probably down.');
                    if (err.message.data) {
                        var except = err.message.data;
                        error_body = except.message || except.arguments || error_body;
                    }
                    self.gui.show_popup('error', {
                        'title': _t('Error: Could not Save Changes'),
                        'body': error_body,
                    });
                });
            } else {
                this._super();
            }
        },
    });

    /* --------------------------------------*\
     THE INVOICES LIST
     ======================================
     Displays the list of invoices and allows the cashier
     to reoder and rewrite the invoices.
     */
    var InvoicesListScreenWidget = screens.ScreenWidget.extend({
        template: 'InvoicesListScreenWidget',
        init: function (parent, options) {
            this._super(parent, options);
        },
        show: function () {
            var self = this;

            this._super();
            this.renderElement();
            this.$('.order-details-contents').empty();
            this.$('.order-list').parent().scrollTop(0);
            this.$('.back').click(function () {
                self.gui.back();
            });

            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.connect(this.$('.invoices_search'));
            }

            this.$('.invoices_search').on('keyup', function () {
                self.perform_search(this.value);
            });

            this.$('.searchbox .search-clear').click(function () {
                self.clear_search();
            });
            this.$('.order-list-contents').on('click', '.order-line', function (e) {
                self.line_select(e, $(this), parseInt($(this).data('id')));
            });
            this.render_list(this.pos.db.pos_all_orders);
        },
        perform_search: function (query) {
            var self = this,
                search_criteria = self.pos.config.order_search_criteria,
                allOrders = this.pos.db.pos_all_orders,
                filteredOrders = [];

            if ($.trim(query) === "") {
                this.render_list(allOrders);
            } else {
                _.each(allOrders, function (order) {
                    _.each(search_criteria, function (criteria) {
                        if (order[criteria]) {
                            // The property partner_id in order object is an Array, the value to compare is in index 1
                            if (_.isArray(order[criteria])) {
                                if (order[criteria][1].toLowerCase().indexOf(query.toLowerCase()) > -1) {
                                    filteredOrders.push(order);
                                    return true;
                                }
                            } else if (order[criteria].toLowerCase().indexOf(query.toLowerCase()) > -1) {
                                filteredOrders.push(order);
                                return true;
                            }
                        }
                    });
                });

                this.render_list(_.uniq(filteredOrders));
            }
        },
        clear_search: function () {
            this.$('.invoices_search')[0].value = '';
            this.$('.invoices_search').focus();
            this.render_list(this.pos.db.pos_all_orders);
        },
        render_list: function (orders) {
            var self = this;
            var contents = this.$('.order-list-contents');

            contents.empty();

            if (!orders) {
                return;
            }

            this.display_order_details('hide');
            orders.forEach(function (order) {
                contents.append(QWeb.render('InvoicesLine', {widget: self, order: order}));
            });
        },
        close: function () {
            this._super();
            this.$('.order-list-contents').off('click', '.order-line');
            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.hide();
            }
        },
        line_select: function (event, $line, id) {
            var self = this;
            var order = self.pos.db.order_by_id[id];

            this.$('.order-list .lowlight').removeClass('lowlight');
            if ($line.hasClass('highlight')) {
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.display_order_details('hide');
            } else {
                var y;

                this.$('.order-list .highlight').removeClass('highlight');
                $line.addClass('highlight');
                this.selected_tr_element = $line;
                y = event.pageY - $line.parent().offset().top;
                this.display_order_details('show', order, y);
            }
        },
        display_order_details: function (visibility, order, clickpos) {
            var self = this;
            var contents = this.$('.order-details-contents');
            var parent = this.$('.order-list').parent();
            var scroll = parent.scrollTop();
            var height = contents.height();
            var new_height = 0;
            var orderlines = [];
            var payment_ids = [];

            if (visibility === 'show') {
                var sumQty = 0;
                order.lines.forEach(function (line_id) {
                    var line = self.pos.db.line_by_id[line_id];
                    orderlines.push(line);
                    sumQty += line.qty - line.l10n_do_line_qty_returned;
                });

                if (sumQty === 0) {
                    order.refunded = true;
                    order.l10n_do_return_status = 'fully_returned';
                }
                contents.empty();
                contents.append($(QWeb.render('OrderDetails',
                    {
                        widget: this,
                        order: order,
                        orderlines: orderlines,
                        payment_ids: payment_ids,
                    })));
                new_height = contents.height();
                if (!this.details_visible) {
                    if (clickpos < scroll + new_height + 20) {
                        parent.scrollTop(clickpos - 20);
                    } else {
                        parent.scrollTop(parent.scrollTop() + new_height);
                    }
                } else {
                    parent.scrollTop(parent.scrollTop() - height + new_height);
                }
                this.$("#close_order_details").on("click", function () {
                    self.display_order_details('hide');
                });
                self.$("#refund").on("click", function () {
                    var message = '';
                    var non_returnable_products = false;
                    var original_orderlines = [];
                    var allow_return = true;
                    var orders = self.pos.get_order_list();

                    // Mostramos la pantalla con la orden si ya esta en proceso de creacion
                    for (var n in orders) {
                        var _order = orders[n];

                        if (_order.l10n_do_is_return_order && _order.l10n_do_return_order_id === order.id) {
                            self.pos.set_order(_order);
                            return false;
                        }
                    }
                    if (order.l10n_do_return_status === 'fully_returned') {
                        message = 'No quedan items para devolver en esta orden!!';
                        allow_return = false;
                    }
                    if (allow_return) {
                        order.lines.forEach(function (line_id) {
                            var line = self.pos.db.line_by_id[line_id];
                            var product = self.pos.db.get_product_by_id(line.product_id[0]);

                            if (product == null) {
                                non_returnable_products = true;
                                message = 'Algun(os) producto(s) de esta orden no esta(n) disponible(s) en el Punto de Venta, desea devolver los productos restantes?';
                            } else if (line.qty - line.l10n_do_line_qty_returned > 0) {
                                original_orderlines.push(line);
                            }
                        });
                        if (original_orderlines.length === 0) {
                            self.gui.show_popup('alert', {
                                'title': _t('No se puede devolver esta Orden!!!'),
                                'body': _t("No quedan productos retornables en esta orden. Tal vez los productos son No Retornables o no estan disponibles en el Punto de Venta!!"),
                            });
                        } else if (non_returnable_products) {
                            self.gui.show_popup('confirm', {
                                'title': _t('Warning !!!'),
                                'body': _t(message),
                                confirm: function () {
                                    self.gui.show_popup('refund_order_popup', {
                                        'orderlines': original_orderlines,
                                        'order': order,
                                        'is_partial_return': true,
                                    });
                                },
                            });
                        } else {
                            self.gui.show_popup('refund_order_popup', {
                                'orderlines': original_orderlines,
                                'order': order,
                                'is_partial_return': false,
                            });
                        }
                    } else {
                        self.gui.show_popup('alert', {
                            'title': _t('Warning!!!'),
                            'body': _t(message),
                        });
                    }
                });
            } else if (visibility === 'hide') {
                if (this.selected_tr_element) {
                    this.selected_tr_element.removeClass('highlight');
                    this.selected_tr_element.addClass('lowlight');
                }
                contents.empty();
                if (height > scroll) {
                    contents.css({height: height + 'px'});
                    contents.animate({height: 0}, 400,
                        function () {
                            contents.css({height: ''});
                        });
                } else {
                    parent.scrollTop(parent.scrollTop() - height);
                }
            }

            this.details_visible = visibility === 'show';
        },
    });

    gui.define_screen({name: 'invoiceslist', widget: InvoicesListScreenWidget});

    var OrderRefundPopup = popups.extend({
        template: 'OrderRefundPopup',
        events: {
            'click .button.cancel': 'click_cancel',
            'click #complete_return': 'click_complete_return',
            'click #return_order': 'click_return_order',
        },
        click_complete_return: function () {
            $.each($('.return_qty'), function (index, value) {
                var line_quantity_remaining = parseFloat($(value).find('input').attr('line-qty-remaining'));
                $(value).find('input').val(line_quantity_remaining);
            });
        },
        click_return_order: function () {
            var self = this;
            var all = $('.return_qty');
            var return_lines = {};
            var return_entries_ok = true, is_input_focused = false;

            $.each(all, function (index, value) {
                var input_element = $(value).find('input');
                var line_quantity_remaining = parseFloat(input_element.attr('line-qty-remaining'));
                var line_id = parseFloat(input_element.attr('line-id'));
                var qty_input = parseFloat(input_element.val());

                if (!$.isNumeric(qty_input) || qty_input > line_quantity_remaining || qty_input < 0) {
                    return_entries_ok = false;
                    input_element.css("background-color", "#ff8888;");
                    setTimeout(function () {
                        input_element.css("background-color", "");
                    }, 100);
                    setTimeout(function () {
                        input_element.css("background-color", "#ff8888;");
                    }, 200);
                    setTimeout(function () {
                        input_element.css("background-color", "");
                    }, 300);
                    setTimeout(function () {
                        input_element.css("background-color", "#ff8888;");
                    }, 400);
                    setTimeout(function () {
                        input_element.css("background-color", "");
                    }, 500);
                    if (!is_input_focused) {
                        input_element.select();
                        is_input_focused = true;
                    }
                }

                if (qty_input === 0 && line_quantity_remaining !== 0 && !self.options.is_partial_return) {
                    self.options.is_partial_return = true;
                } else if (qty_input > 0) {
                    return_lines[line_id] = {
                        qty: qty_input,
                        qty_remaining: line_quantity_remaining,
                    };
                    if (line_quantity_remaining !== qty_input && !self.options.is_partial_return) {
                        self.options.is_partial_return = true;
                    }
                }
            });
            if (Object.keys(return_lines).length === 0) {
                self.$("input").css("background-color", "#ff8888;");
                setTimeout(function () {
                    self.$("input").css("background-color", "");
                }, 100);
                setTimeout(function () {
                    self.$("input").css("background-color", "#ff8888;");
                }, 200);
                setTimeout(function () {
                    self.$("input").css("background-color", "");
                }, 300);
                setTimeout(function () {
                    self.$("input").css("background-color", "#ff8888;");
                }, 400);
                setTimeout(function () {
                    self.$("input").css("background-color", "");
                }, 500);
                if (self.$("input").length > 0) {
                    self.$("input:eq(0)").select();
                }
            } else if (return_entries_ok) {
                self.create_return_order(return_lines);
            }
        },
        create_return_order: function (return_lines) {
            var self = this;
            var order = self.options.order;
            var refund_order = {};

            if (Object.keys(return_lines).length === 0) {
                return;
            }

            if (self.options.mode === 'edit') {
                var _order = self.pos.get_order();
                var orderlines = _order.get_orderlines();
                for (var n = orderlines.length - 1; n >= 0; n--) {
                    _order.orderlines.remove(orderlines[n]);
                }
                refund_order = _order;
            } else {
                self.gui.show_screen('products');
                self.pos.add_new_order(); // Crea un nuevo objeto orden del lado del cliente
                refund_order = self.pos.get_order();
                refund_order.l10n_do_is_return_order = true;
                refund_order.l10n_do_return_order_id = order.id;
                refund_order.l10n_do_origin_ncf = order.l10n_latam_document_number;
                refund_order.set_client(self.pos.db.get_partner_by_id(order.partner_id[0]));
                refund_order.set_latam_document_type(
                    self.pos.l10n_latam_document_type_credit_note)
            }
            refund_order.orderlineList = [];
            refund_order.amount_total = 0;
            if (self.options.is_partial_return) {
                refund_order.l10n_do_return_status = 'partially_returned';
            } else {
                refund_order.l10n_do_return_status = 'fully_returned';
            }
            Object.keys(return_lines).forEach(function (line_id) {
                var return_line = return_lines[line_id];
                var line = self.pos.db.line_by_id[line_id];
                var product = self.pos.db.get_product_by_id(line.product_id[0]);
                var qty = -1*parseFloat(return_line.qty);

                refund_order.add_product(product, {
                    quantity: qty,
                    price: line.price_unit,
                    discount: line.discount,
                });
                refund_order.selected_orderline.l10n_do_original_line_id = line.id;
                var apply_discounts = function (price, discount) {
                    return price - (price * Math.max(Math.min(discount, 100), 0))/100;
                };
                var unit_price_with_discounts = apply_discounts(line.price_unit, line.discount);
                var unit_price_with_taxes = line.qty ? parseFloat(line.price_subtotal_incl) / line.qty : 0;
                refund_order.amount_total += unit_price_with_taxes * qty;
                refund_order.orderlineList.push({
                    line_id: line_id,
                    product_id: line.product_id[0],
                    product_name: line.product_id[1],
                    quantity: qty,
                    price: line.price_subtotal_incl,
                    price_unit: unit_price_with_discounts,
                    taxes: qty ? ( unit_price_with_taxes - unit_price_with_discounts ) : 0
                });
            });
            this.click_confirm();
            self.gui.show_screen('payment', null, true);
        },
        show: function (options) {
            var firstInput;

            options = options || {};
            this._super(options);
            this.orderlines = options.orderlines || [];
            this.renderElement();
            firstInput = $('.return_qty input:eq(0)');
            if (firstInput.length) {
                firstInput.select();
            }
        },
    });

    gui.define_popup({
        name: 'refund_order_popup',
        widget: OrderRefundPopup,
    });

    popups.include({
        /**
         * Show the popup
         * @param {(string, Object)} options - The title or optional configuration for the popup.
         * @param {boolean} options.disable_keyboard_handler - Disable the keyboard capture for the payment screen
         * when the popup is opened.
         * @param {string} options.input_name - Indicate the name of text input and is used for show the
         * description of it for the textinput and textarea popups
         * @param {string} options.text_input_value - Indicate the initial value of text input for the textinput
         * and textarea popups
         */
        show: function (options) {
            this._super(options);
        },
        renderElement: function () {
            this._super();
            // Ponemos un valor por defecto al input del popup TextInput o TextArea
            if (["TextInputPopupWidget", "TextAreaPopupWidget"].indexOf(this.template) > -1) {
                var self = this;
                var input = this.$('input,textarea');

                if (input.length > 0) {
                    // Ponemos un valor al input
                    input.val(this.options.text_input_value || '');
                    // Ejecutamos el clic al boton confirm al presionar Enter
                    input.on('keypress', function (event) {
                        if (event.which === 13) {
                            self.click_confirm(this.value);
                            event.stopPropagation();
                            event.preventDefault();
                        }
                    });
                }
            }
        },
        close: function () {
            this._super();
            if (this.options && this.options.hasOwnProperty('text_input_value')) {
                this.options.text_input_value = '';
            }
        },
    });

    // TODO CHECK THIS
    // screens.ActionpadWidget.include({
    //     renderElement: function () {
    //         var self = this,
    //             $payButton,
    //             payButtonClickSuper;
    //
    //         this._super.apply(this, arguments);
    //         $payButton = this.$('.pay');
    //         // TODO CHECK THIS
    //         // payButtonClickSuper = $payButton.getEvent('click', 0);
    //         $payButton.off('click');
    //         $payButton.on("click", function () {
    //             var invoicing = self.pos.config.module_account;
    //             var order = self.pos.get_order();
    //             var client = self.pos.get_client();
    //             var popupErrorOptions = '';
    //
    //             if (order.get_total_with_tax() <= 0) {
    //                 popupErrorOptions = {
    //                     'title': 'Cantidad de articulos a pagar',
    //                     'body': 'La orden esta vacia o el total pagar es RD$0.00',
    //                 };
    //             } else if (client && !client.vat) {
    //                 if (["fiscal", "gov", "special"].indexOf(client.sale_fiscal_type) > -1) {
    //                     popupErrorOptions = {
    //                         'title': 'Para el tipo de comprobante',
    //                         'body': 'No puede crear una factura con crédito fiscal si el cliente ' +
    //                         'no tiene RNC o Cédula.\n\nPuede pedir ayuda para que el cliente sea ' +
    //                         'registrado correctamente si este desea comprobante fiscal.',
    //                     };
    //                 } else if (invoicing && order.get_total_without_tax() >= 250000) {
    //                     popupErrorOptions = {
    //                         'title': 'Factura sin Cedula de Cliente',
    //                         'body': 'El cliente debe tener una cedula si el total de la factura ' +
    //                         'es igual o mayor a RD$250,000.00 o mas',
    //                     };
    //                 }
    //             }
    //             if (popupErrorOptions) {
    //                 self.gui.show_popup('error', popupErrorOptions);
    //             } else if (payButtonClickSuper) {
    //                 payButtonClickSuper.apply(this, arguments);
    //             }
    //         });
    //     },
    // });

    gui.Gui.include({

        /**
         * Allows the keyboard capture for the current screen
         */
        __enable_keyboard_handler: function () {
            var current_screen = this.current_screen;

            if (!current_screen || !current_screen.keyboard_handler) {
                return;
            }

            $('body').on('keypress', current_screen.keyboard_handler);
            $('body').on('keydown', current_screen.keyboard_keydown_handler);
        },

        /**
         * Remove the keyboard capture for the current screen
         */
        __disable_keyboard_handler: function () {
            var current_screen = this.current_screen;

            if (!current_screen || !current_screen.keyboard_handler) {
                return;
            }

            $('body').off('keypress', current_screen.keyboard_handler);
            $('body').off('keydown', current_screen.keyboard_keydown_handler);
            window.document.body.removeEventListener('keypress', current_screen.keyboard_handler);
            window.document.body.removeEventListener('keydown', current_screen.keyboard_keydown_handler);
        },
        show_popup: function (name, options) {
            if (options && options.disable_keyboard_handler === true) {
                this.__disable_keyboard_handler();
            }
            return this._super(name, options);
        },
        close_popup: function () {
            if (this.current_popup && this.current_popup.options &&
                this.current_popup.options.disable_keyboard_handler === true) {
                this.__enable_keyboard_handler();
            }
            this._super();
        },
    });
});
