odoo.define('ncf_pos.screens', function (require) {
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');
    var form_common = require('web.form_common');

    var QWeb = core.qweb;
    var _t = core._t;




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

        }
        ,
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


            $(self.action_buttons.set_fiscal_position.$el).remove()


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

            });
        },

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
