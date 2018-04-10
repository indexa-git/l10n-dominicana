odoo.define('ncf_pos.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var _t = core._t;

    screens.ClientListScreenWidget.include({
        display_client_details: function (visibility, partner, clickpos) {
            var self = this;

            this._super(visibility, partner, clickpos);
            var name_input = this.$('input[name$=\'name\']');
            var $rnc = $("input[name$='vat']");
            var $sale_fiscal_type = $("select[name$='sale_fiscal_type']");

            name_input.autocomplete({
                source: "/dgii_ws/",
                minLength: 3,
                select: function (event, ui) {
                    name_input.val(ui.item.name);
                    $rnc.val(ui.item.rnc);
                    $sale_fiscal_type.val("fiscal");

                    return false;
                }
            });
        }
    });

    /*--------------------------------------*\
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
            this.$('.button').click(function () {
                self.perform_search(self.$('.invoices_search').val());
            });
            this.$('.back').click(function () {
                self.gui.back();
            });

            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.connect(this.$('.invoices_search'));
            }
            this.$('.invoices_search').on('keypress', function (event) {
                if (event.which === 13)
                    self.perform_search(this.value);
            }).focus();
            this.$('.searchbox .search-clear').click(function () {
                self.clear_search();
            });
            this.$('.order-list-contents').on('click', '.order-line', function (e) {
                self.line_select(e, $(this), parseInt($(this).data('id')));
            });
            this.render_list(this.pos.db.pos_all_orders);
        },
        perform_search: function (query) {
            var self = this;

            if ($.trim(query) == "") {
                this.render_list(this.pos.db.pos_all_orders);
            } else {
                var allOrders = this.pos.db.pos_all_orders;
                var orders = [];

                for (var i in allOrders) {
                    if (String(allOrders[i].number).toLowerCase().indexOf(String(query).toLowerCase()) > -1)
                        orders.push(allOrders[i]);
                }

                if (orders.length > 0) {
                    this.render_list(orders);
                } else {
                    rpc.query({
                        model: 'pos.order',
                        method: 'order_search_from_ui',
                        args: [query]
                    }, {})
                        .then(function (result) {
                            var orders = result && result.orders || [];
                            var orderlines = result && result.orderlines || [];

                            orders.forEach(function (order) {
                                var obj = self.pos.db.order_by_id[order.id];

                                if (!obj)
                                    self.pos.db.pos_all_orders.push(order);
                                self.pos.db.order_by_id[order.id] = order;
                            });
                            self.pos.db.pos_all_order_lines.concat(orderlines);
                            orderlines.forEach(function (line) {
                                self.pos.db.line_by_id[line.id] = line;
                            });

                            self.render_list(orders);
                        });
                }
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

            //if (order.is_return_order)
            //    return false;
            this.$('.order-list .lowlight').removeClass('lowlight');
            if ($line.hasClass('highlight')) {
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.display_order_details('hide');
            }
            else {
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
            var statements = [];

            if (visibility === 'show') {
                var sumQty = 0;

                order.lines.forEach(function (line_id) {
                    var line = self.pos.db.line_by_id[line_id];

                    orderlines.push(line);
                    sumQty += (line.qty - line.line_qty_returned);
                });
                if (sumQty == 0) {
                    order.refunded = true;
                    order.return_status = 'Fully-Returned'
                }
                contents.empty();
                contents.append($(QWeb.render('OrderDetails',
                    {
                        widget: this,
                        order: order,
                        orderlines: orderlines,
                        statements: statements
                    })));
                new_height = contents.height();
                if (!this.details_visible) {
                    if (clickpos < scroll + new_height + 20) {
                        parent.scrollTop(clickpos - 20);
                    }
                    else
                        parent.scrollTop(parent.scrollTop() + new_height);
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

                    //Mostramos la pantalla con la orden si ya esta en proceso de creacion
                    for (var n in orders) {
                        var _order = orders[n];

                        if (_order.is_return_order && _order.return_order_id == order.id) {
                            self.pos.set_order(_order);
                            return false;
                        }
                    }
                    if (order.return_status == 'Fully-Returned') {
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
                            } else if (product.not_returnable) {
                                non_returnable_products = true;
                                message = 'Esta orden contiene algunos productos No Retornables, desea devolver los otros productos?';
                            } else if (line.qty - line.line_qty_returned > 0) {
                                original_orderlines.push(line);
                            }
                        });
                        if (original_orderlines.length == 0) {
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
            }
            else if (visibility === 'hide') {
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
                }
                else
                    parent.scrollTop(parent.scrollTop() - height);
            }

            this.details_visible = (visibility === 'show');
        }
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

                if (qty_input == 0 && line_quantity_remaining != 0 && !self.options.is_partial_return) {
                    self.options.is_partial_return = true;
                }
                else if (qty_input > 0) {
                    return_lines[line_id] = {
                        qty: qty_input,
                        qty_remaining: line_quantity_remaining
                    };
                    if (line_quantity_remaining != qty_input && !self.options.is_partial_return) {
                        self.options.is_partial_return = true;
                    }
                }
            });
            if (Object.keys(return_lines).length == 0) {
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
                if (self.$("input").length > 0)
                    self.$("input:eq(0)").select();
            }
            else if (return_entries_ok)
                self.create_return_order(return_lines);
        },
        create_return_order: function (return_lines) {
            var self = this;
            var order = self.options.order;
            var refund_order = {};

            if (Object.keys(return_lines).length == 0) return;

            if (self.options.mode == 'edit') {
                var _order = self.pos.get_order();
                var orderlines = _order.get_orderlines();

                for (var n = orderlines.length - 1; n >= 0; n--) {
                    _order.orderlines.remove(orderlines[n]);
                }
                refund_order = _order;
            } else {
                self.pos.add_new_order(); //Crea un nuevo objeto orden del lado del cliente
                refund_order = self.pos.get_order();
                refund_order.is_return_order = true;
                refund_order.return_order_id = order.id;
                refund_order.set_client(self.pos.db.get_partner_by_id(order.partner_id[0]));
            }
            refund_order.orderlineList = [];
            refund_order.amount_total = 0;
            if (self.options.is_partial_return)
                refund_order.return_status = 'Partially-Returned';
            else
                refund_order.return_status = 'Fully-Returned';
            Object.keys(return_lines).forEach(function (line_id) {
                var return_line = return_lines[line_id];
                var line = self.pos.db.line_by_id[line_id];
                var product = self.pos.db.get_product_by_id(line.product_id[0]);
                var qty = parseFloat(return_line.qty);

                refund_order.add_product(product, {
                    quantity: qty,
                    price: line.price_unit,
                    discount: line.discount
                });
                refund_order.selected_orderline.original_line_id = line.id;
                refund_order.amount_total += parseFloat(line.price_subtotal_incl) * qty;
                refund_order.orderlineList.push({
                    line_id: line_id,
                    product_id: line.product_id[0],
                    product_name: line.product_id[1],
                    quantity: qty,
                    price: line.price_subtotal_incl
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
            if (firstInput.length)
                firstInput.select()
        },
    });

    gui.define_popup({
        name: 'refund_order_popup',
        widget: OrderRefundPopup
    });

    popups.include({
        renderElement: function () {
            this._super();
            //Ponemos un valor por defecto al input del popup TextInput o TextArea
            if (["TextInputPopupWidget", "TextAreaPopupWidget"].indexOf(this.template) > -1 &&
                this.options.text_input_value) {
                var input = this.$('input,textarea');

                if (input.length > 0)
                    input.val(this.options.text_input_value);
            }
        }
    });

    screens.PaymentScreenWidget.include({
        show: function () {
            var self = this;
            var order = this.pos.get_order();
            var paymentContents = this.$('.left-content, .right-content, .back, .next');
            var refundContents = this.$('.refund-confirm-content, .cancel, .confirm');

            this._super();
            if (order && order.is_return_order) {
                var refundConfirm = this.$('.refund-confirm-content');

                paymentContents.addClass('oe_hidden');
                refundContents.removeClass('oe_hidden');
                this.$('.top-content h1').html(_t('Refund Order'));
                refundConfirm.empty();
                refundConfirm.append(QWeb.render('OrderRefundConfirm', {widget: this, order: order}));
                if (order.paymentlines.length == 0) {
                    var cashregister = this.pos.cashregisters[0];

                    for (var n in this.pos.cashregisters) {
                        if (this.pos.cashregisters[n].journal.type.toLowerCase() == "cash") {
                            cashregister = this.pos.cashregisters[n];
                            break;
                        }
                    }
                    order.add_paymentline(cashregister);
                    order.selected_paymentline.set_amount(order.get_total_with_tax()); //Add paymentline for total+tax
                }
                this.order_changes();
            } else {
                paymentContents.removeClass('oe_hidden');
                refundContents.addClass('oe_hidden');
            }
            this.$('.button.js_invoice').remove();
            this.$('.confirm').click(function () {
                self.gui.show_popup('confirm', {
                    title: _t('Create') + ' ' + _t('Refund Order'),
                    body: _t('Are you sure you want to create this refund order?'),
                    confirm: function () {
                        self.validate_order();
                    },
                });
                return false;
            }).addClass('highlight');
            this.$('.edit').click(function () {
                var original_order = self.pos.db.order_by_id[order.return_order_id];
                var original_orderlines = [];
                var return_product = {};

                order.orderlineList.forEach(function (obj) {
                    return_product[obj.product_id] = obj.quantity;
                });
                original_order.lines.forEach(function (line_id) {
                    var line = $.extend({}, self.pos.db.line_by_id[line_id]);
                    var product = self.pos.db.get_product_by_id(line.product_id[0]);

                    if (product != null && !product.not_returnable && line.qty - line.line_qty_returned > 0) {
                        line.current_return_qty = return_product[line.product_id[0]] || 0;
                        original_orderlines.push(line);
                    }
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
                    }
                });
                return false;
            });
            this.$('.cancel').click(function () {
                $('.order-selector .deleteorder-button').click();
                return false;
            });
        },
        validate_order: function (force_validation) {
            // TODO: refactor this
            var order = this.pos.get_order();
            var client = this.pos.get_client();

            function has_client_vat(client) {
                return client.vat;
            }

            function has_client_fiscal_type(client, fiscal_types) {
                return _.contains(fiscal_types, client.sale_fiscal_type) && !has_client_vat(client);
            }

            if (!client) {
                if (this.pos.config.iface_invoicing) {
                    this.gui.show_popup('error', {
                        'title': 'Error: Factura sin Cliente',
                        'body': 'Debe seleccionar un cliente para poder realizar el pago, o utilizar el cliente por defecto; de no tener un cliente por defecto, pida ayuda a su encargado para que lo establezca.',
                        'cancel': function () {
                            this.gui.show_screen('products');
                        }
                    });

                    return false;
                }
            } else {
                if (has_client_fiscal_type(client, ["fiscal", "gov", "special"]) && !has_client_vat(client)) {
                    this.gui.show_popup('error', {
                        'title': 'Error: Para el tipo de comprobante',
                        'body': 'No puede crear una factura con crédito fiscal si el cliente no tiene RNC o Cédula. Puede pedir ayuda para que el cliente sea registrado correctamente si este desea comprobante fiscal',
                        'cancel': function () {
                            this.gui.show_screen('products');
                        }
                    });
                    return false;
                }

                if (this.pos.config.iface_invoicing && order.get_total_without_tax() >= 50000 && !has_client_vat(client)) {
                    this.gui.show_popup('error', {
                        'title': 'Error: Factura sin Cedula de Cliente',
                        'body': 'El cliente debe tener una cedula si el total de la factura es igual o mayor a RD$50,000 o mas',
                        'cancel': function () {
                            this.gui.show_screen('products');
                        }
                    });

                    return false;
                }
            }

            this._super();
        },
        init: function (parent, options) {
            this._super(parent, options);
            //Agregamos una forma de pago personalizada para lanzar el popup de Nota de Credito
            this.pos.cashregisters.push({
                journal_id: [10001, 'Nota de Credito'],
                journal: {type: 'cash', id: 10001, sequence: 10001},
                css_class: 'highlight',
                show_popup: true,
                popup_name: 'alert',
                popup_options: {title: 'Crear Nota de Credito'}
            });
        },
        click_paymentmethods: function (id) {
            for (var i = 0; i < this.pos.cashregisters.length; i++) {
                var cashregister = this.pos.cashregisters[i];

                //Evaluamos que sea una forma de pago personalizada que lanza un popup
                if (cashregister.journal_id[0] === id && cashregister.show_popup === true) {
                    this.gui.show_popup(cashregister.popup_name || 'alert', cashregister.popup_options);
                    return false;
                }
            }
            this._super(id);
        }
    });

    screens.ActionpadWidget.include({
        renderElement: function () {
            var self = this;
            this._super();

            this.$('.pay').on("click", function () {
                var order = self.pos.get_order();
                var has_valid_product_lot = _.every(order.orderlines.models, function (line) {
                    return line.has_valid_product_lot();
                });
                if (!has_valid_product_lot) {
                    self.gui.show_popup('confirm', {
                        'title': _t('Empty Serial/Lot Number'),
                        'body': _t('One or more product(s) required serial/lot number.'),
                        confirm: function () {
                            self.gui.show_screen('payment');
                        },
                    });
                } else {
                    self.gui.show_screen('payment');
                }

                // Here begin the method extension
                // TODO: refactor this
                var client = self.pos.get_client();

                function has_client_vat(client) {
                    return client.vat;
                }

                function has_client_fiscal_type(client, fiscal_types) {
                    return _.contains(fiscal_types, client.sale_fiscal_type) && !has_client_vat(client);
                }

                if (order.get_total_with_tax() <= 0) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Cantidad de articulos a pagar',
                        'body': 'La orden esta vacia, no existen articulos a pagar.',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                } else {
                    order.orderlines.find(function (line) {
                        if (line.get_price_with_tax() < 0) {
                            self.gui.show_popup('error', {
                                'title': 'Error: Precio de producto',
                                'body': 'Ningun producto puede tener precio menor a RD$0',
                                'cancel': function () {
                                    self.gui.show_screen('products');
                                }
                            });

                            return true;
                        }
                    });
                }

                if (!client) {
                    if (self.pos.config.iface_invoicing) {
                        self.gui.show_popup('error', {
                            'title': 'Error: Factura sin Cliente',
                            'body': 'Debe seleccionar un cliente para poder realizar el pago, o utilizar el cliente por defecto; de no tener un cliente por defecto, pida ayuda a su encargado para que lo establezca.',
                            'cancel': function () {
                                self.gui.show_screen('products');
                            }
                        });

                        return false;
                    }
                } else {
                    if (has_client_fiscal_type(client, ["fiscal", "gov", "special"]) && !has_client_vat(client)) {
                        self.gui.show_popup('error', {
                            'title': 'Error: Para el tipo de comprobante',
                            'body': 'No puede crear una factura con crédito fiscal si el cliente no tiene RNC o Cédula. Puede pedir ayuda para que el cliente sea registrado correctamente si este desea comprobante fiscal',
                            'cancel': function () {
                                self.gui.show_screen('products');
                            }
                        });
                        return false;
                    }

                    if (self.pos.config.iface_invoicing && order.get_total_without_tax() >= 50000 && !has_client_vat(client)) {
                        self.gui.show_popup('error', {
                            'title': 'Error: Factura sin Cedula de Cliente',
                            'body': 'El cliente debe tener una cedula si el total de la factura es igual o mayor a RD$50,000 o mas',
                            'cancel': function () {
                                self.gui.show_screen('products');
                            }
                        });

                        return false;
                    }
                }

                // Here end the method extension
            });

            this.$('.set-customer').click(function () {
                self.gui.show_screen('clientlist');
            });
        }
    });

    gui.Gui.include({
        /**
         * Allows the keyboard capture for the current screen
         */
        __enable_keyboard_handler: function () {
            var current_screen = this.current_screen;

            if (!current_screen || !current_screen.keyboard_handler) return;

            window.document.body.addEventListener('keypress', current_screen.keyboard_handler);
            window.document.body.addEventListener('keydown', current_screen.keyboard_keydown_handler);
        },
        /**
         * Remove the keyboard capture for the current screen
         */
        __disable_keyboard_handler: function () {
            var current_screen = this.current_screen;

            if (!current_screen || !current_screen.keyboard_handler) return;

            $('body').off('keypress', current_screen.keyboard_handler);
            $('body').off('keydown', current_screen.keyboard_keydown_handler);
            window.document.body.removeEventListener('keypress', current_screen.keyboard_handler);
            window.document.body.removeEventListener('keydown', current_screen.keyboard_keydown_handler);
        },
        show_popup: function (name, options) {
            if (options && options.disable_keyboard_handler === true)
                this.__disable_keyboard_handler();
            return this._super(name, options);
        },
        close_popup: function () {
            if (this.current_popup && this.current_popup.options &&
                this.current_popup.options.disable_keyboard_handler === true)
                this.__enable_keyboard_handler();
            this._super();
        }
    });
});