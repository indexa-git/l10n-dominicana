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
            var name_input, rnc_input, sale_fiscal_type_ddl;
            var sale_fiscal_type_vat = this.pos.sale_fiscal_type_vat;

            this._super(visibility, partner, clickpos);
            name_input = this.$('input[name$=\'name\']');
            rnc_input = this.$("input[name$='vat']");
            sale_fiscal_type_ddl = this.$("select[name$='sale_fiscal_type']");
            name_input.autocomplete({
                source: "/dgii_ws/",
                minLength: 3,
                delay: 200,
                select: function (event, ui) {
                    name_input.val(ui.item.name);
                    rnc_input.val(ui.item.rnc);
                    sale_fiscal_type_ddl.val("fiscal");

                    return false;
                },
                response: function (event, ui) {
                    // selecting the first item if the result is only one
                    if (Array.isArray(ui.content) && ui.content.length == 1 && $.isNumeric(name_input.val())) {
                        var input = $(this);

                        ui.item = ui.content[0];
                        input.data('ui-autocomplete')._trigger('select', 'autocompleteselect', ui);
                        input.autocomplete('close');
                        input.blur();
                    }
                }
            });
            sale_fiscal_type_ddl.change(function () {
                var len = rnc_input.val().length;

                if (len == 9 && sale_fiscal_type_vat.rnc.indexOf(this.value) == -1) {
                    sale_fiscal_type_ddl.val(sale_fiscal_type_vat.rnc[0]);
                } else if (len == 11 && sale_fiscal_type_vat.ced.indexOf(this.value) == -1) {
                    sale_fiscal_type_ddl.val(sale_fiscal_type_vat.ced[0]);
                } else if (len != 9 && len != 11) {
                    if (len > 0) {
                        sale_fiscal_type_ddl.val(sale_fiscal_type_vat.other[0]);
                    } else if (sale_fiscal_type_vat.no_vat.indexOf(this.value) == -1) {
                        sale_fiscal_type_ddl.val(sale_fiscal_type_vat.no_vat[0]);
                    }
                }
            });
            name_input.blur(function () {
                this.value = $.trim(this.value).toUpperCase();
            });
            rnc_input.blur(function () {
                this.value = $.trim(this.value).toUpperCase();
                sale_fiscal_type_ddl.trigger('change');
            });
            if (visibility === 'show' && partner) {
                // Highlighting the row of the displayed partner in the client list
                if (this.old_client && this.old_client !== partner) {
                    var clOldClient = this.partner_cache.get_node(this.old_client.id);
                    var clientLine = this.partner_cache.get_node(partner.id);

                    if (clOldClient) {
                        clOldClient.classList.remove('highlight');
                    }
                    if (clientLine) {
                        clientLine.classList.add('highlight');
                    }
                }
            } else if (visibility === 'edit') {
                name_input.focus();
            }
        },
        save_client_details: function (partner) {
            var self = this;
            var _super = this._super.bind(this);
            var rnc_input = this.$("input[name='vat']"),
                rnc = rnc_input.val();
            var name_input = this.$('input[name$=\'name\']');
            var sale_fiscal_type_ddl = this.$("select[name$='sale_fiscal_type']"),
                sale_fiscal_type = sale_fiscal_type_ddl.val();
            var fieldsRequired = [];

            if (!name_input.val()) {
                fieldsRequired.push({label: 'Name', elem: name_input});
            }
            if (!sale_fiscal_type) {
                fieldsRequired.push({label: 'NCF', elem: sale_fiscal_type_ddl});
            }
            if (this.pos.sale_fiscal_type_vat.no_vat.indexOf(sale_fiscal_type) == -1 && !rnc) {
                fieldsRequired.push({label: 'Tax ID', elem: rnc_input});
            }
            if (fieldsRequired.length > 0) {
                var fields = fieldsRequired.map(function (obj) {
                    return '\n - ' + _t(obj.label);
                });
                this.gui.show_popup('error', {
                    'title': _t('Save') + ' ' + _t('Customer'),
                    'body': _t('You must fill in the required fields:') + '\n' + fields.join(' '),
                    cancel: function () {
                        fieldsRequired[0].elem.focus();
                    }
                });
            } else if (rnc && (rnc.length == 9 || rnc.length == 11)) {
                $.ajax('/validate_rnc/', {
                    dataType: 'json',
                    type: 'GET',
                    timeout: 3000,
                    data: {'rnc': rnc}
                }).done(function (data) {
                    console.info("Validando RNC con WS DGII", data);
                    if (data.is_valid === false) {
                        self.gui.show_popup('error', {
                            'title': _t('Validating') + ' ' + _t('Tax ID') + ' ' + rnc,
                            'body': _t('Tax ID') + ' ' + _t('is invalid'),
                            cancel: function () {
                                rnc_input.focus();
                            }
                        });
                    } else {
                        if (data.info && data.info.name) {
                            name_input.val(data.info.name);
                        }
                        _super(partner);
                    }
                }).fail(function (request, error) {
                    console.error("Validando RNC con WS DGII", request);
                    self.gui.show_popup('error', {
                        'title': _t('Validating') + ' ' + _t('Tax ID') + ' ' + rnc,
                        'body': _t(request.statusText + '\n' +
                            ((error.data && error.data.message) || error.message || "")),
                        cancel: function () {
                            rnc_input.focus();
                        }
                    });
                    _super(partner);
                });
            } else {
                this._super(partner);
            }
        },
        saved_client_details: function (partner_id) {
            if (this.editing_client) {
                var clientLine = this.partner_cache.get_node(partner_id);

                // Removing the row of the modified partner to allow the update
                // of the partner's information in the client list
                if (clientLine) {
                    this.partner_cache.clear_node(partner_id);
                }
            }
            this._super.apply(this, arguments);
        },
        toggle_save_button: function () {
            var $button = this.$('.button.next');

            this._super.apply(this, arguments);
            // Hide the deselect customer button if the pos generate invoices
            if ($button && this.pos.config.iface_invoicing === true &&
                this.editing_client !== true && !this.new_client) {
                $button.addClass('oe_hidden');
            }
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

            if (!orders) return;

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
                refund_order.origin_ncf = order.number;

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
            //Ponemos un valor por defecto al input del popup TextInput o TextArea
            if (["TextInputPopupWidget", "TextAreaPopupWidget"].indexOf(this.template) > -1) {
                var self = this;
                var input = this.$('input,textarea');

                if (input.length > 0) {
                    //Ponemos un valor al input
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
            if (this.options && this.options.hasOwnProperty('text_input_value'))
                this.options.text_input_value = '';
        }
    });

    screens.PaymentScreenWidget.include({
        init: function (parent, options) {
            var self = this,
                popup_options = {
                    title: 'Digite el número de NCF de la Nota de Crédito',
                    disable_keyboard_handler: true,
                    input_name: 'ncf',
                    text_input_value: '',
                    confirm: function (input_value) {
                        var msg_error = "";

                        rpc.query({
                            model: 'pos.order',
                            method: 'credit_note_info_from_ui',
                            args: [input_value]
                        }, {})
                            .then(function (result) {
                                var residual = parseFloat(result.residual) || 0;

                                if (result.id === false) {
                                    msg_error = _t("La nota de credito no existe.");
                                } else if (residual < 1) {
                                    msg_error = _t("El balance de la Nota de Credito es 0.");
                                }
                                else {
                                    var order = self.pos.get_order();
                                    var cashregister = self.pos.cashregisters_by_id[10001];
                                    var paymentline = order.paymentlines.find(function (pl) {
                                        return pl.note == input_value
                                    });

                                    if (paymentline) {
                                        msg_error = "Esta Nota de Credito ya esta aplicada a la Orden";
                                    }
                                    else {
                                        order.add_paymentline(cashregister);
                                        order.selected_paymentline.credit_note_id = result.id;
                                        order.selected_paymentline.note = input_value;
                                        order.selected_paymentline.set_amount(residual); //Add paymentline for residual
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
                                    }
                                });
                            });
                    }
                };

            this._super(parent, options);
            this.orderValidationDate = null;
            // Set the popup options for the payment method Credit Note
            for (var n in this.pos.cashregisters) {
                if (this.pos.cashregisters[n].journal.id == 10001) {
                    this.pos.cashregisters[n].popup_options = popup_options;
                    break;
                }
            }
        },
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
                this.$('.button.confirm').click(function () {
                    self.gui.show_popup('confirm', {
                        title: _t('Create') + ' ' + _t('Refund Order'),
                        body: _t('Are you sure you want to create this refund order?'),
                        confirm: function () {
                            self.validate_order();
                        }
                    });
                    return false;
                }).addClass('highlight');
                this.$('.button.cancel').click(function () {
                    $('.order-selector .deleteorder-button').click();
                    return false;
                });
                this.$('.button-custom.edit').click(function () {
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
            } else {
                paymentContents.removeClass('oe_hidden');
                refundContents.addClass('oe_hidden');
            }
            this.$('.button.js_invoice').remove();
            //improving the keyboard handling method
            this.gui.__disable_keyboard_handler();
            this.gui.__enable_keyboard_handler();
        },
        /**
         * Get the next ncf sequence
         *
         * @param {object} order - pos order object
         * @returns {Promise} - Promise object that return the next ncf sequence
         */
        get_next_ncf: function (order) {
            var self = this,
                args = [
                    order.uid,
                    order.get_client().sale_fiscal_type,
                    this.pos.config.invoice_journal_id[0],
                    order.is_return_order
                ],
                dfd = $.Deferred();

            console.info("Executing get_next_ncf", new Date());
            if (!order) {
                console.error("get_next_ncf", "The order is missing");
                dfd.reject("get_next_ncf - The order is missing");
            } else {
                dfd = rpc.query({
                    model: 'pos.order',
                    method: 'get_next_ncf',
                    args: args
                }, {
                    timeout: 3000
                });

                dfd.done(function (next_ncf) {
                    var ncfs = self.pos.db.load('ncfs', []);

                    order.ncf = next_ncf;
                    ncfs.push({validatedNcf: next_ncf, orderUid: order.uid});
                    self.pos.db.save('ncfs', ncfs);
                    console.info("Order NCF Validated", {ncf: next_ncf, uid: order.uid});
                }).fail(function (request) {
                    order.ncf = '';
                    console.error("get_next_ncf", request);
                });
            }
            return dfd.promise();
        },
        /**
         * Making some things about validation and calling to backend to get the ncf
         */
        validate_order: function (force_validation) {
            if (this.order_is_valid(force_validation)) {
                var self = this,
                    now = new Date(),
                    orderValidationDate = (this.orderValidationDate || null);

                //blocking the execution of this method for 5 seconds or until the execution is completed
                if (orderValidationDate && ((now - orderValidationDate) <= 5000)) {
                    console.info("Failed attempt to execute validate_order", new Date());
                } else {
                    var invoicing = self.pos.config.iface_invoicing,
                        order = self.pos.get_order(),
                        client = self.pos.get_client(),
                        popupErrorOptions = null;

                    this.orderValidationDate = new Date();
                    console.info("Executing validate_order", this.orderValidationDate);
                    if (!client && invoicing) {
                        popupErrorOptions = {
                            'title': 'Factura sin Cliente',
                            'body': 'Debe seleccionar un cliente para poder realizar el pago, o ' +
                            'utilizar el cliente por defecto.\n\nDe no tener un cliente por defecto, ' +
                            'pida ayuda a su encargado para que lo establezca.'
                        };
                    } else if (client && !client.vat) {
                        if (["fiscal", "gov", "special"].indexOf(client.sale_fiscal_type) > -1) {
                            popupErrorOptions = {
                                'title': 'Para el tipo de comprobante',
                                'body': 'No puede crear una factura con crédito fiscal si el cliente ' +
                                'no tiene RNC o Cédula.\n\nPuede pedir ayuda para que el cliente sea ' +
                                'registrado correctamente si este desea comprobante fiscal.',
                            };
                        } else if (invoicing && order.get_total_without_tax() >= 50000) {
                            popupErrorOptions = {
                                'title': 'Factura sin Cedula de Cliente',
                                'body': 'El cliente debe tener una cedula si el total de la factura ' +
                                'es igual o mayor a RD$50,000.00 o mas',
                            };
                        }
                    }
                    if (popupErrorOptions) {
                        console.warn(popupErrorOptions.title, {message: popupErrorOptions.body});
                        self.gui.show_popup('error', popupErrorOptions);
                        self.orderValidationDate = null;
                    } else {
                        this.get_next_ncf(order).always(function () {
                            console.info("Finishing Order Validation", new Date());
                            self.finalize_validation();
                            self.orderValidationDate = null;
                        });
                    }
                }
            }
        },
        click_paymentmethods: function (id) {
            //Validamos que la orden tenga saldo pendiente antes de agregar una nueva linea de pago
            if (this.pos.get_order().get_due() <= 0) {
                this.gui.show_popup('alert', {
                    title: _t("Payment"),
                    body: _t("This order has no pending balance."),
                    disable_keyboard_handler: true
                });
            } else {
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    var cashregister = this.pos.cashregisters[i];

                    //Evaluamos si es una forma de pago especial que abre un popup
                    if (cashregister.journal_id[0] === id && cashregister.show_popup === true) {
                        this.gui.show_popup(cashregister.popup_name || 'alert', cashregister.popup_options);
                        return false;
                    }
                }
                this._super(id);
            }
        },
        payment_input: function (input) {
            var order = this.pos.get_order();

            //Evitamos que se pueda cambiar el monto de la Nota de Credito
            if (order.selected_paymentline && order.selected_paymentline.cashregister.id == 10001)
                return false;
            this._super(input);
        },
        /** Update customer information when another customer is selected */
        customer_changed: function () {
            var client = this.pos.get_client();
            var clientFiscalType = (client && client.sale_fiscal_type) || '';

            this._super.apply(this, arguments);
            this.$('.sale_fiscal_type_label').text(clientFiscalType ?
                this.pos.get_sale_fiscal_type(clientFiscalType).name : '');
        }
    });

    screens.ActionpadWidget.include({
        renderElement: function () {
            var self = this,
                $payButton,
                payButtonClickSuper;

            this._super.apply(this, arguments);
            $payButton = this.$('.pay');
            payButtonClickSuper = $payButton.getEvent('click', 0);
            $payButton.off('click');
            $payButton.on("click", function () {
                var invoicing = self.pos.config.iface_invoicing;
                var order = self.pos.get_order();
                var client = self.pos.get_client();
                var popupErrorOptions = '';

                if (order.get_total_with_tax() <= 0) {
                    popupErrorOptions = {
                        'title': 'Cantidad de articulos a pagar',
                        'body': 'La orden esta vacia o el total pagar es RD$0.00'
                    };
                } else if (!client && invoicing) {
                    popupErrorOptions = {
                        'title': 'Factura sin Cliente',
                        'body': 'Debe seleccionar un cliente para poder realizar el pago, o ' +
                        'utilizar el cliente por defecto.\n\nDe no tener un cliente por defecto, ' +
                        'pida ayuda a su encargado para que lo establezca.'
                    };
                } else if (client && !client.vat) {
                    if (["fiscal", "gov", "special"].indexOf(client.sale_fiscal_type) > -1) {
                        popupErrorOptions = {
                            'title': 'Para el tipo de comprobante',
                            'body': 'No puede crear una factura con crédito fiscal si el cliente ' +
                            'no tiene RNC o Cédula.\n\nPuede pedir ayuda para que el cliente sea ' +
                            'registrado correctamente si este desea comprobante fiscal.',
                        };
                    } else if (invoicing && order.get_total_without_tax() >= 250000) {
                        popupErrorOptions = {
                            'title': 'Factura sin Cedula de Cliente',
                            'body': 'El cliente debe tener una cedula si el total de la factura ' +
                            'es igual o mayor a RD$50,000.00 o mas',
                        };
                    }
                }
                if (popupErrorOptions) {
                    self.gui.show_popup('error', popupErrorOptions);
                } else if (payButtonClickSuper) {
                    payButtonClickSuper.apply(this, arguments);
                }
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

            $('body').on('keypress', current_screen.keyboard_handler);
            $('body').on('keydown', current_screen.keyboard_keydown_handler);
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