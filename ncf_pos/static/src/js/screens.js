odoo.define('ncf_pos.screens', function (require) {
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');
    var form_common = require('web.form_common');

    var QWeb = core.qweb;
    var _t = core._t;

    //var _PaymentScreenWidget = screens.PaymentScreenWidget.prototype;
    screens.PaymentScreenWidget.include({
        init: function (parent, options) {
            var self = this;
            this._super(parent, options);
            this.keyboard_keydown_handler = function (event) {
                if (event.keyCode === 8 || event.keyCode === 46) {
                    self.keyboard_handler(event);
                }
            };
            this.keyboard_handler = function (event) {
                var key = '';

                if (event.type === "keypress") {
                    if (event.keyCode === 13) { // Enter
                        self.validate_order();
                    } else if (event.keyCode === 190 || // Dot
                        event.keyCode === 110 ||  // Decimal point (numpad)
                        event.keyCode === 188) { // Comma
                        key = '.';
                    } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                        key = '' + (event.keyCode - 48);
                    } else if (event.keyCode === 45) { // Minus
                        key = '-';
                    } else if (event.keyCode === 43) { // Plus
                        key = '+';
                    }
                } else { // keyup/keydown
                    if (event.keyCode === 46) { // Delete
                        key = 'CLEAR';
                    } else if (event.keyCode === 8) { // Backspace
                        key = 'BACKSPACE';
                    }
                }

                self.payment_input(key);

            };
        },
        check_if_real_stock_valuation: function (order) {
            var self = this;
            var order = this.pos.get_order();
            var product_ids = [];

            _.each(order.orderlines.models, function (line) {
                product_ids.push(line.product.id)
            });

            posOrderModel = new Model('pos.order');
            return posOrderModel.call('check_if_real_stock_valuation', [product_ids])
                .then(function (res) {
                    if (res) {
                        self.gui.show_popup('selection', {
                            title: _t('No puede terminar la order productos sin costos definidos!'),
                            list: res,
                            confirm: function () {
                                self.gui.close_popup();
                            }
                        });
                        return false;
                    } else {
                        return true
                    }
                });

        },
        validate_order: function (force_validation) {
            var self = this;
            var order = this.pos.get_order();
            var client = order.get_client();
            var can_print = false;

            if (client === undefined) {
                self.gui.show_popup('confirm', {
                    title: _t('Cliente no seleccionado!'),
                    body: "Debe de seleccionar cliente para validar la factura!",
                    confirm: function () {
                        self.gui.close_popup();
                    }
                });
                return false;
            } else {
                this.check_if_real_stock_valuation().then(function (res) {
                    if (res) {
                        self.finish_validate_order(force_validation);
                    }
                });
            }
        },
        finish_validate_order: function (force_validation) {
            var self = this;

            var order = this.pos.get_order();

            // FIXME: this check is there because the backend is unable to
            // process empty orders. This is not the right place to fix it.
            if (order.get_orderlines().length === 0) {
                this.gui.show_popup('error', {
                    'title': _t('Empty Order'),
                    'body': _t('There must be at least one product in your order before it can be validated'),
                });
                return;
            }

            // get rid of payment lines with an amount of 0, because
            // since accounting v9 we cannot have bank statement lines
            // with an amount of 0
            order.clean_empty_paymentlines();

            var plines = order.get_paymentlines();
            for (var i = 0; i < plines.length; i++) {
                if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
                    this.pos_widget.screen_selector.show_popup('error', {
                        'message': _t('Negative Bank Payment'),
                        'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                    });
                    return;
                }
            }

            if (!order.is_paid() || this.invoicing) {
                return;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.gui.show_popup('error', {
                        title: _t('Cannot return change without a cash payment method'),
                        body: _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return;
                }
            }

            // if the change is too large, it's probably an input error, make the user confirm.
            if (!force_validation && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
                this.gui.show_popup('confirm', {
                    title: _t('Please Confirm Large Amount'),
                    body: _t('Are you sure that the customer wants to  pay') +
                    ' ' +
                    this.format_currency(order.get_total_paid()) +
                    ' ' +
                    _t('for an order of') +
                    ' ' +
                    this.format_currency(order.get_total_with_tax()) +
                    ' ' +
                    _t('? Clicking "Confirm" will validate the payment.'),
                    confirm: function () {
                        self.validate_order('confirm');
                    },
                });
                return;
            }

            if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) {

                this.pos.proxy.open_cashbox();
            }

            if (order.is_to_invoice()) {
                var invoiced = this.pos.push_and_invoice_order(order);
                this.invoicing = true;

                invoiced.fail(function (error) {
                    self.invoicing = false;
                    if (error.message === 'Missing Customer') {
                        self.gui.show_popup('confirm', {
                            'title': _t('Please select the Customer'),
                            'body': _t('You need to select the customer before you can invoice an order.'),
                            confirm: function () {
                                self.gui.show_screen('clientlist');
                            },
                        });
                    } else if (error.code < 0) {        // XmlHttpRequest Errors
                        self.gui.show_popup('error', {
                            'title': _t('The order could not be sent'),
                            'body': _t('Check your internet connection and try again.'),
                        });
                    } else if (error.code === 200) {    // OpenERP Server Errors
                        self.gui.show_popup('error-traceback', {
                            'title': error.data.message || _t("Server Error"),
                            'body': error.data.debug || _t('The server encountered an error while receiving your order.'),
                        });
                    } else {                            // ???
                        self.gui.show_popup('error', {
                            'title': _t("Unknown Error"),
                            'body': _t("The order could not be sent to the server due to an unknown error"),
                        });
                    }
                });

                invoiced.done(function () {
                    self.invoicing = false;
                    order.finalize();
                });
            } else {
                this.pos.push_order(order);
                this.gui.show_screen('receipt');
            }
        },
        renderElement: function () {
            var self = this;
            this._super();
            this.$(".js_credit_note").click(function () {
                self.apply_credit();
            });
        },
        payment_input: function (input) {
            var order = this.pos.get_order();
            if (order.selected_paymentline) {
                if (order.selected_paymentline.get_type() == "credit") {
                    return
                }
            }

            this._super(input);

        },
        apply_credit: function () {
            var self = this;
            var order = self.pos.get_order();
            var default_partner_id = self.pos.config.default_partner_id;
            var partner_id = order.get_client();
            var credit = 0;
            var PosOrderModel = new Model("pos.order");

            if (order.get_total_with_tax() == 0) {
                return
            }

            if (partner_id.id == default_partner_id[0]) {
                self.gui.show_popup("alert", {
                    title: "Alerta",
                    body: "No esta permitido aplicar creditos de devoluciones a facturas sin antes asignarle un cliente," +
                    "Si la nota de credito que desea aplicar no tiene cliente asignado solicite ayuda de un supervisor!!"
                });
            }

            PosOrderModel.call("get_partner_credit", [order.get_client().id])
                .then(function (result) {

                    if (!result || order.get_due() == 0) {
                        return
                    }

                    credit = result;
                    if (result > order.get_due()) {
                        credit = order.get_due()
                    }

                    var cashregisters = self.pos.cashregisters[0];
                    self.pos.get_order().add_paymentline(cashregisters);
                    order.selected_paymentline.set_amount(credit);
                    order.selected_paymentline.set_type("credit");
                    self.order_changes();
                    self.render_paymentlines();
                    self.$('.paymentline.selected .edit').text(self.format_currency_no_symbol(credit));
                }).fail(function () {
                self.gui.show_popup("alert", {
                    title: "Alerta", body: "El PTV no pudo conectar al servidor!!"
                });
            });

        },
        render_paymentlines: function () {
            var self = this;
            var order = this.pos.get_order();
            if (!order) {
                return;
            }

            var lines = order.get_paymentlines();
            var due = order.get_due();
            var extradue = 0;
            if (due && lines.length && due !== order.get_due(lines[lines.length - 1])) {
                extradue = due;
            }
            _.each(lines, function (line) {
                if (line.get_type() == "credit") {
                    line.name = "Nota de crédito";
                }
            });

            this.$('.paymentlines-container').empty();
            var lines = $(QWeb.render('PaymentScreen-Paymentlines', {
                widget: this,
                order: order,
                paymentlines: lines,
                extradue: extradue,
            }));

            lines.on('click', '.delete-button', function () {
                self.click_delete_paymentline($(this).data('cid'));
            });

            lines.on('click', '.paymentline', function () {
                self.click_paymentline($(this).data('cid'));
            });

            lines.appendTo(this.$('.paymentlines-container'));
        }
    });

    screens.ProductScreenWidget.include({
        start: function () {
            this._super();
            var self = this;
            var fiscal_position = self.action_buttons.set_fiscal_position;

            if (fiscal_position === undefined) {
                window.location.replace("/web");
                alert("Debe asignar posiciones fiscales a esta terminal.");
            } else {
                $(self.action_buttons.set_fiscal_position.$el).remove();
            }

            $(".refund-cancel-button").click(function () {
                self.cancel_refund();
            });

            $(".refund-button").click(function () {
                self.refund_order();
            });

            $(".refund-money-button").click(function () {
                self.ask_refund_money();
            });
        },
        cancel_refund: function () {
            var self = this;
            self.pos.delete_current_order();
        },
        ask_refund_money: function () {
            var self = this;
            var order = self.pos.get_order();
            if (order.is_empty()) {
                self.gui.show_popup("alert", {title: "Alerta", body: "No hay ningun productos para devolver!!"});
                return
            }
            order.set_order_type("draft_refund_money");
            self.pos.push_order(order);
            self.gui.show_screen('products');
            self.pos.delete_current_order();

        },
        refund_order: function () {
            var self = this;
            var order = self.pos.get_order();
            if (order.is_empty()) {
                self.gui.show_popup("alert", {title: "Alerta", body: "No hay ningun productos para devolver!!"});
                return
            }

            self.pos.push_order(order);
            self.gui.show_screen('receipt');
        },
        click_product: function (product) {
            var self = this;
            var StockProductLot = new Model("stock.production.lot");
            if (product.tracking != 'none') {
                self.gui.show_popup('textinput', {
                    title: "Este producto requiere número de Serie/Lote para venderlo.",
                    confirm: function (value) {
                        StockProductLot.query(["id"]).filter([['name', '=', value], ['product_id', '=', product.id]])
                            .limit(1)
                            .all()
                            .then(function (res) {
                                if (res.length == 1) {
                                    self.extended_click_product(product, {"prodlot_id": res[0].id})
                                }
                            });
                    }
                });

            } else {
                self.extended_click_product(product, {})
            }

        },
        extended_click_product: function (product, options) {
            if (product.to_weight && this.pos.config.iface_electronic_scale) {
                this.gui.show_screen('scale', {product: product});
            } else {
                this.pos.get_order().add_product(product, options);
            }
        }
    });

    screens.ReceiptScreenWidget.include({

        render_receipt: function () {
            var self = this;
            var order = this.pos.get_order();
            var client = order.attributes.client;


            new Model('pos.order').call("get_fiscal_data", [order.name]).then(function (result) {

                order.set_ncf(result.ncf);
                var invoice_type = result.fiscal_type_name;

                order.save_to_db();
                self.$('.pos-receipt-container').html(QWeb.render('PosTicket', {
                    widget: self,
                    order: order,
                    invoice_type: invoice_type,
                    ncf: order.get_ncf(),
                    client: client,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines()
                }));

            })
        }

    });


    //Button for quotations
    var QuotationActionWidget = screens.ActionButtonWidget.extend({
        template: 'QuotationActionWidget',
        button_click: function () {
            var self = this;
            self.gui.show_popup('QuotationPopup');
        }
    });

    screens.define_action_button({
        'name': 'qoutation',
        'widget': QuotationActionWidget,
        'condition': function () {
            return true;
        }

    });


});
