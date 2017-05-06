odoo.define('ncf_pos.pos_order_return', function (require) {
    "use strict";
    var pos_orders = require('ncf_pos.pos_orders');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var chrome = require('point_of_sale.chrome');
    var QWeb = core.qweb;
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
    var PopupWidget = require('point_of_sale.popups');
    var _t = core._t;
    var SuperOrder = models.Order;
    var SuperOrderline = models.Orderline.prototype;
    var formats = require('web.formats');
    models.load_fields('product.product', 'not_returnable');
    models.load_fields('res.partner', 'sale_fiscal_type');

    var MyMessagePopup = PopupWidget.extend({
        template: 'MyMessagePopup'
    });
    gui.define_popup({name: 'my_message', widget: MyMessagePopup});

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

                if (qty_input == 0 && line_quantity_remaining != 0 && !self.options.is_partial_return)
                    self.options.is_partial_return = true;
                else if (qty_input > 0) {
                    return_dict[line_id] = qty_input;
                    if (line_quantity_remaining != qty_input && !self.options.is_partial_return)
                        self.options.is_partial_return = true;
                    else if (!self.options.is_partial_return)
                        self.options.is_partial_return = false;
                }
            });
            if (return_entries_ok)
                self.create_return_order(return_dict);
        },
        create_return_order: function (return_dict) {
            var self = this;
            var order = self.options.order;
            var orderlines = self.options.orderlines;
            var current_order = self.pos.get_order();
            if (Object.keys(return_dict).length > 0) {
                self.chrome.widget.order_selector.neworder_click_handler();
                var refund_order = self.pos.get_order();
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
                    refund_order.is_return_order = true;
                } else {
                    refund_order.return_status = 'Fully-Returned';
                    refund_order.return_order_id = order.id;
                    refund_order.is_return_order = true;
                }
                self.pos.set_order(current_order);
                self.pos.set_order(refund_order);
                self.gui.show_screen('payment');
            }
            else {
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
    gui.define_popup({name: 'return_products_popup', widget: OrderReturnPopup});

    models.load_models([{
        model: 'account.bank.statement.line',
        fields: ['id', 'journal_id', 'amount'],
        loaded: function (self, statements) {
            self.db.all_statements = statements;
            self.db.statement_by_id = {};
            statements.forEach(function (statement) {
                self.db.statement_by_id[statement.id] = statement;
            });

            self.sale_fiscal_type = [{"code": "final", "name": "Consumidor final"},
                {"code": "fiscal", "name": "Para crédito fiscal"},
                {"code": "gov", "name": "Gubernamental"},
                {"code": "special", "name": "Regimenes especiales"}]

        },
    }]);

    models.load_models({
        model: 'pos.order',
        fields: ['id', 'name', 'date_order', 'partner_id', 'lines', 'pos_reference', 'invoice_id', 'is_return_order', 'return_order_id', 'return_status', 'statement_ids', 'amount_total'],
        domain: function (self) {
            var domain_list = [];
            if (self.config.load_orders_after_this_date)
                domain_list = [['date_order', '>', self.config.load_orders_from], ['state', 'not in', ['draft', 'cancel']], ['is_return_order', '=', false]]
            else
                domain_list = [['session_id', '=', self.pos_session.name], ['state', 'not in', ['draft', 'cancel']], ['is_return_order', '=', false]]
            return domain_list;
        },
        loaded: function (self, wk_order) {
            self.db.pos_all_orders = wk_order;
            self.db.order_by_id = {};
            wk_order.forEach(function (order) {
                self.db.order_by_id[order.id] = order;
            });
        }
    });

    models.load_models({
        model: 'pos.order.line',
        fields: ['product_id', 'order_id', 'qty', 'discount', 'price_unit', 'price_tax', 'price_subtotal_incl', 'price_subtotal', 'line_qty_returned'],
        domain: function (self) {
            var order_lines = []
            var orders = self.db.pos_all_orders;
            for (var i = 0; i < orders.length; i++) {
                order_lines = order_lines.concat(orders[i]['lines']);
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
        },
    });


    screens.OrderWidget.include({
        update_summary: function () {
            this._super();
            var order = this.pos.get_order();
            if (!order.get_orderlines().length) {
                return;
            }
            var total = order ? order.get_total_with_tax() : 0;
            var taxes = order ? total - order.get_total_without_tax() : 0;
            if (order.is_return_order) {
                total *= -1;
                taxes *= -1;
            }
            this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
            this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);
        },
    });

    screens.ClientListScreenWidget.include({
        show: function () {
            var self = this;
            self._super();

            if (self.pos.get_order().is_return_order) {
                self.gui.back();
            }

            $('.view_all_order').on('click', function () {
                self.gui.show_screen('wk_order', {
                    'customer_id': this.id
                });
            });
        }
    });

    screens.PaymentScreenWidget.include({
        show: function () {
            var self = this;
            self._super();

            $('#order_note').on('focus', function () {
                window.document.body.removeEventListener('keypress', self.keyboard_handler);
                window.document.body.removeEventListener('keydown', self.keyboard_keydown_handler);
            });

            $('#order_note').on('focusout', function () {
                window.document.body.addEventListener('keypress', self.keyboard_handler);
                window.document.body.addEventListener('keydown', self.keyboard_keydown_handler);
            });
        },

        payment_input: function (input) {
            var newbuf = this.gui.numpad_input(this.inputbuffer, input, {'firstinput': this.firstinput});

            this.firstinput = (newbuf.length === 0);
            if (this.gui.has_popup()) {
                return;
            }

            if (newbuf !== this.inputbuffer) {
                this.inputbuffer = newbuf;
                var order = this.pos.get_order();
                if (order.selected_paymentline) {
                    var amount = this.inputbuffer;

                    if (this.inputbuffer !== "-") {
                        amount = formats.parse_value(this.inputbuffer, {type: "float"}, 0.0);
                    }
                    var due_amount = parseFloat(this.$('.paymentline.selected .col-due').text().replace(',', ''));
                    if (amount > due_amount && order.is_return_order) {
                        this.inputbuffer = due_amount.toString();
                        order.selected_paymentline.set_amount(due_amount);
                        this.order_changes();
                        this.render_paymentlines();
                        this.$('.paymentline.selected .edit').text(this.format_currency_no_symbol(due_amount));
                    }
                    else {
                        order.selected_paymentline.set_amount(amount);
                        this.order_changes();
                        this.render_paymentlines();
                        this.$('.paymentline.selected .edit').text(this.format_currency_no_symbol(amount));
                    }
                }
            }
        },
    });

    screens.ProductScreenWidget.include({
        show: function () {
            var self = this;
            var current_order = self.pos.get_order();
            $("#cancel_refund_order").on("click", function () {
                $(".deleteorder-button").trigger("click");
            });
            this._super();

            this.product_categories_widget.reset_category();
            this.numpad.state.reset();
            $('#all_orders').on('click', function () {
                self.gui.show_screen('wk_order', {});
            });

            if (self.pos.get_order().is_return_order) {
                $('.product').css("pointer-events", "none");
                $('.product').css("opacity", "0.4");
                $('#refund_order_notify').show();
                $('#cancel_refund_order').show();
                self.$('.numpad-backspace').css("pointer-events", "none");
            }
            else {
                $('.product').css("pointer-events", "");
                $('.product').css("opacity", "");
                $('#refund_order_notify').hide();
                $('#cancel_refund_order').hide();
                self.$('.numpad-backspace').css("pointer-events", "");
            }
        }
    });

    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            SuperOrder.prototype.initialize.call(this, attributes, options);

            this.return_status = '-';
            this.is_return_order = false;
            this.return_order_id = false;
            if (!this.get_client()) {
                var default_partner_id = this.pos.db.get_partner_by_id(this.pos.config.default_partner_id[0]);
                this.set_client(default_partner_id);
            }
        },
        export_as_JSON: function () {
            var self = this;
            var loaded = SuperOrder.prototype.export_as_JSON.call(this);
            var current_order = self.pos.get_order();
            if (self.pos.get_order() != null) {
                loaded.is_return_order = current_order.is_return_order;
                loaded.return_status = current_order.return_status;
                loaded.return_order_id = current_order.return_order_id;
                loaded.order_note = self.get_order_note();
            }
            return loaded;
        },
        get_order_note: function () {
            return $("#order_note").val();
        }
    });

    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            this.line_qty_returned = 0;
            this.original_line_id = null;
            SuperOrderline.initialize.call(this, attr, options);
        },
        export_as_JSON: function () {
            var self = this;
            var loaded = SuperOrderline.export_as_JSON.call(this);
            loaded.line_qty_returned = self.line_qty_returned;
            loaded.original_line_id = self.original_line_id;
            return loaded;
        }
    });

    screens.NumpadWidget.include({
        clickAppendNewChar: function (event) {
            var self = this;
            if (!self.pos.get_order().is_return_order)
                this._super(event);
        },
        clickSwitchSign: function () {
            var self = this;
            if (!self.pos.get_order().is_return_order)
                this._super(event);
        },
    });

    pos_orders.include({
        show: function () {
            var self = this;
            this._super();

            this.details_visible = false;
            this.selected_tr_element = null;
            self.$('.wk-order-list-contents').delegate('.wk-order-line', 'click', function (event) {
                self.line_select(event, $(this), parseInt($(this).data('id')));
            });

            var contents = this.$('.order-details-contents');
            contents.empty();
            var parent = self.$('.wk_order_list').parent();
            parent.scrollTop(0);

            //reorder
            this.$('.wk-order-list-contents').delegate('.wk_reorder_content', 'click', function(event){
				var order_line_data = self.pos.db.pos_all_order_lines;
				var order = self.pos.get_order();
				for(var i=0; i<order_line_data.length;i++) {
					if(order_line_data[i].order_id[0] == this.id)
					{
						var product = self.pos.db.get_product_by_id(order_line_data[i].product_id[0]);
						order.add_product(product,{quantity:order_line_data[i].qty});
					}
				}
				self.gui.show_screen('products');
			});

            //reprint
            this.$('.wk-order-list-contents').delegate('.wk_reprint_content', 'click', function(event){
				var order_line_data = self.pos.db.pos_all_order_lines;
				for(var i=0; i<order_line_data.length;i++) {
					if(order_line_data[i].order_id[0] == this.id)
					{
						var product = self.pos.db.get_product_by_id(order_line_data[i].product_id[0]);
						order.add_product(product,{quantity:order_line_data[i].qty});
					}
				}
				self.gui.show_screen('products');
			});

        },
        line_select: function (event, $line, id) {
            var self = this;
            var order = self.pos.db.order_by_id[id];
            this.$('.wk_order_list .lowlight').removeClass('lowlight');
            if ($line.hasClass('highlight')) {
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.display_order_details('hide', order);
            } else {
                this.$('.wk_order_list .highlight').removeClass('highlight');
                $line.addClass('highlight');
                self.selected_tr_element = $line;
                var y = event.pageY - $line.parent().offset().top;
                self.display_order_details('show', order, y);
            }
        },
        display_order_details: function (visibility, order, clickpos) {
            var self = this;
            var contents = this.$('.order-details-contents');
            var parent = this.$('.wk_order_list').parent();
            var scroll = parent.scrollTop();
            var height = contents.height();
            var orderlines = [];
            var statements = [];
            var journal_ids_used = [];
            if (visibility === 'show') {
                order.lines.forEach(function (line_id) {
                    orderlines.push(self.pos.db.line_by_id[line_id]);
                });
                order.statement_ids.forEach(function (statement_id) {
                    var statement = self.pos.db.statement_by_id[statement_id];
                    statements.push(statement);
                    journal_ids_used.push(statement.journal_id[0]);
                });
                contents.empty();
                contents.append($(QWeb.render('OrderDetails', {
                    widget: this,
                    order: order,
                    orderlines: orderlines,
                    statements: statements
                })));
                var new_height = contents.height();
                if (!this.details_visible) {
                    if (clickpos < scroll + new_height + 20) {
                        parent.scrollTop(clickpos - 20);
                    } else {
                        parent.scrollTop(parent.scrollTop() + new_height);
                    }
                } else {
                    parent.scrollTop(parent.scrollTop() - height + new_height);
                }
                this.details_visible = true;
                self.$("#close_order_details").on("click", function () {
                    self.selected_tr_element.removeClass('highlight');
                    self.selected_tr_element.addClass('lowlight');
                    self.details_visible = false;
                    self.display_order_details('hide', null);
                });
                self.$("#wk_refund").on("click", function () {
                    var order_list = self.pos.db.pos_all_orders;
                    var order_line_data = self.pos.db.pos_all_order_lines;
                    var order_id = this.id;
                    var message = '';
                    var non_returnable_products = false;
                    var original_orderlines = [];
                    var allow_return = true;
                    if (order.return_status == 'Fully-Returned') {
                        message = 'Lo sentimos, no puede devolver el mismo pedido dos veces !!'
                        allow_return = false;
                    }
                    if (allow_return) {
                        order.lines.forEach(function (line_id) {
                            var line = self.pos.db.line_by_id[line_id];
                            var product = self.pos.db.get_product_by_id(line.product_id[0]);
                            if (product.not_returnable) {
                                non_returnable_products = true;
                                message = 'Este pedido contiene algunos productos no retornables, ¿desea devolver otros productos?'
                            }
                            else if (line.qty - line.line_qty_returned > 0)
                                original_orderlines.push(line);
                        });
                        if (original_orderlines.length == 0) {
                            self.gui.show_popup('my_message', {
                                'title': _t('¡No puede devolver esta orden !!!'),
                                'body': _t("¡No hay productos retornables para esta orden!"),
                            });
                        }
                        else if (non_returnable_products) {
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
                        }
                        else {
                            self.gui.show_popup('return_products_popup', {
                                'orderlines': original_orderlines,
                                'order': order,
                                'is_partial_return': false,
                            });
                        }
                    }
                    else {
                        self.gui.show_popup('my_message', {
                            'title': _t('Error!!!'),
                            'body': _t(message),
                        });
                    }
                });
            }
            if (visibility === 'hide') {
                contents.empty();
                if (height > scroll) {
                    contents.css({height: height + 'px'});
                    contents.animate({height: 0}, 400, function () {
                        contents.css({height: ''});
                    });
                } else {
                    parent.scrollTop(parent.scrollTop() - height);
                }
                this.details_visible = false;
            }
        }
    });
});
