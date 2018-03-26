odoo.define('ncf_pos.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var PopupWidget = require('point_of_sale.popups');
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
     The invoiceslist displays the list of invoices,
     and allows the cashier to reoder and rewrite the invoices.
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

                            orders.forEach(function (order) {
                                var obj = self.pos.db.order_by_id[order.id];

                                if (!obj)
                                    self.pos.db.pos_all_orders.push(order);
                                self.pos.db.order_by_id[order.id] = order;
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
                var rowHtml = QWeb.render('InvoicesLine', {widget: self, order: order});

                contents.append(rowHtml);
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
            var orderlines = order && order.lines;
            var statements = [];

            if (visibility === 'show') {
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
                }
                else
                    parent.scrollTop(parent.scrollTop() - height + new_height);

                this.$("#close_order_details").on("click", function () {
                    self.display_order_details('hide');
                });
                self.$("#refund").on("click", function () {
                    var message = '';
                    var non_returnable_products = false;
                    var original_orderlines = [];
                    var allow_return = true;
                    if (order.return_status == 'Fully-Returned') {
                        message = 'No quedan items para devolver en esta orden!!';
                        allow_return = false;
                    }
                    if (allow_return) {
                        order.lines.forEach(function (line) {
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
                                    self.gui.show_popup('return_products_popup', {
                                        'orderlines': original_orderlines,
                                        'order': order,
                                        'is_partial_return': true,
                                    });
                                },
                            });
                        } else {
                            self.gui.show_popup('return_products_popup', {
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

    var OrderReturnPopup = PopupWidget.extend({
        template: 'OrderReturnPopup',
        events: {
            'click .button.cancel': 'click_cancel',
            'click #complete_return': 'click_complete_return',
            'click #return_order': 'click_return_order',
        },
        click_return_order: function () {
            var self = this;
            var all = $('.return_qty');
            var return_dict = {};
            var return_entries_ok = true;
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
                }

                if (qty_input == 0 && line_quantity_remaining != 0 && !self.options.is_partial_return) {
                    self.options.is_partial_return = true;
                }
                else if (qty_input > 0) {
                    return_dict[line_id] = qty_input;
                    if (line_quantity_remaining != qty_input && !self.options.is_partial_return) {
                        self.options.is_partial_return = true;
                    }
                    else if (!self.options.is_partial_return) {
                        self.options.is_partial_return = false;
                    }
                }
            });
            if (return_entries_ok) {
                self.create_return_order(return_dict);
            }
        },
        create_return_order: function (return_dict) {
            var self = this;
            var order = self.options.order;
            var orderlines = self.options.orderlines;
            var current_order = self.pos.get_order();
            if (Object.keys(return_dict).length > 0) {
                self.chrome.widget.order_selector.neworder_click_handler();
                var refund_order = self.pos.get_order();
                refund_order.is_return_order = true;
                refund_order.set_client(self.pos.db.get_partner_by_id(order.partner_id[0]));
                Object.keys(return_dict).forEach(function (line_id) {
                    var line = self.pos.db.line_by_id[line_id];
                    var product = self.pos.db.get_product_by_id(line.product_id[0]);
                    refund_order.add_product(product, {
                        quantity: parseFloat(return_dict[line_id]),
                        price: line.price_unit,
                        discount: line.discount
                    });
                    refund_order.selected_orderline.original_line_id = line.id;
                });
                if (self.options.is_partial_return) {
                    refund_order.return_status = 'Partially-Returned';
                    refund_order.return_order_id = order.id;
                } else {
                    refund_order.return_status = 'Fully-Returned';
                    refund_order.return_order_id = order.id;
                }
                self.pos.set_order(refund_order);
                self.gui.show_screen('payment');
            } else {
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
            }
        },
        click_complete_return: function () {
            var self = this;
            var all = $('.return_qty');
            $.each(all, function (index, value) {
                var line_quantity_remaining = parseFloat($(value).find('input').attr('line-qty-remaining'));
                $(value).find('input').val(line_quantity_remaining);
            });
        },
        show: function (options) {
            options = options || {};
            var self = this;
            this._super(options);
            this.orderlines = options.orderlines || [];
            this.renderElement();
        },
    });
    gui.define_popup({
        name: 'return_products_popup',
        widget: OrderReturnPopup
    });

    screens.PaymentScreenWidget.include({
        show: function () {
            this._super();
            $(".button.js_invoice").remove();
        },
        validate_order: function(force_validation) {
            // TODO: refactor this
            var order = this.pos.get_order();
            var client = this.pos.get_client();
            function has_client_vat(client) {
                return client.vat;
            }
            function has_client_fiscal_type(client, fiscal_types) {
                return _.contains(fiscal_types, client.sale_fiscal_type) && !has_client_vat(client);
            }

            if (!client){
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
                
                if(order.get_total_with_tax() <= 0) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Cantidad de articulos a pagar',
                        'body': 'La orden esta vacia, no existen articulos a pagar.',
                        'cancel': function() {
                            self.gui.show_screen('products');
                        }
                    });
                } else {
                    order.orderlines.find(function (line) {
                        if (line.get_price_with_tax() < 0) {
                            self.gui.show_popup('error', {
                                'title': 'Error: Precio de producto',
                                'body': 'Ningun producto puede tener precio menor a RD$0',
                                'cancel': function() {
                                    self.gui.show_screen('products');
                                }
                            });

                            return true;
                        }
                    });
                }

                if (!client){
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
});