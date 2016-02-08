odoo.define('ncf_pos.screens', function (require) {
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');
    var PopUpWidget = require('point_of_sale.popups');
    var form_common = require('web.form_common');

    var QWeb = core.qweb;
    var _t = core._t;

    screens.PaymentScreenWidget.include({
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
                    title: "Alerta", body: "No esta permitido aplicar creditos de devoluciones a facturas sin antes asignarle un cliente," +
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
            new Model('pos.order').call("get_ncf", [order.name]).then(function (result) {


                order.set_ncf(result.ncf);

                var ncf = order.get_ncf();
                var ncf_reference = order.get_credit_ncf();
                var fiscal_type = ncf.slice(9, 11);
                if (ncf_reference) {
                    var fiscal_reference_type = ncf_reference.slice(9, 11);
                }
                var invoice_type;

                switch (fiscal_type) {
                    case "01":
                        invoice_type = "FACTURA CON VALOR FISCAL";
                        order.set_fiscal_type("fiscal");
                        break;
                    case "02":
                        invoice_type = "FACTURA PARA CONSUMIDOR FINAL";
                        order.set_fiscal_type("final");
                        break;
                    case "14":
                        invoice_type = "FACTURA GUBERNAMENTAL";
                        order.set_fiscal_type("fiscal");
                        break;
                    case "15":
                        invoice_type = "FACTURA PARA REGIMENES ESPECIALES";
                        order.set_fiscal_type("special");
                        break;
                    case "04":
                        if (fiscal_reference_type == "01" || fiscal_reference_type == "13"){
                            order.set_fiscal_type("fiscal_note");
                        } else if (fiscal_reference_type == "02"){
                            order.set_fiscal_type("final_note");
                        } else {
                            order.set_fiscal_type("special_note");
                        }
                        invoice_type = "NOTA DE CREDITO";
                    default:
                        invoice_type = "";
                }

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


    var QuotationPopupWidget = PopUpWidget.extend({
        template: 'QuotationPopupWidget',
        show: function (opts) {
            var self = this;
            this._super(opts);
            var order = self.pos.get_order();

            this.$("#print_pdf").click(function () {
                self.report_action("print", order);
            });

            this.$("#send_mail").click(function () {
                self.report_action("send", order);
            });

            this.$("#quotation_cancel").click(function () {
                self.gui.close_popup();
            })

        },
        report_action: function (action, order) {
            var self = this;
            order.set_quotation_type(action);
            var invoiced = self.push_and_quotation_order(order);

            invoiced.fail(function (error) {
                self.invoicing = false;

                if (error.message === 'Missing Customer') {
                    self.pos.gui.show_popup('confirm', {
                        'title': _t('Please select the Customer'),
                        'body': _t('You need to select the customer before you can invoice an order.'),
                        confirm: function () {
                            self.gui.show_screen('clientlist');
                        },
                    });
                }
                else if (error.message === 'Missing Customer Email') {
                    self.pos.gui.show_popup('confirm', {
                        'title': _t('Please select the Customer'),
                        'body': _t('You need to select the customer before you can invoice an order.'),
                        confirm: function () {
                            self.gui.show_screen('clientlist');
                        },
                    });
                }
                else if (error.code < 0) {        // XmlHttpRequest Errors
                    self.pos.gui.show_popup('error', {
                        'title': _t('The order could not be sent'),
                        'body': _t('Check your internet connection and try again.'),
                    });
                } else if (error.code === 200) {    // OpenERP Server Errors
                    self.pos.gui.show_popup('error-traceback', {
                        'title': error.data.message || _t("Server Error"),
                        'body': error.data.debug || _t('The server encountered an error while receiving your order.'),
                    });
                } else {                            // ???
                    self.pos.gui.show_popup('error', {
                        'title': _t("Unknown Error"),
                        'body': _t("The order could not be sent to the server due to an unknown error"),
                    });
                }
            });


            invoiced.done(function (res) {

                order.finalize();
                self.gui.close_popup();

            });

        },
        push_and_quotation_order: function (order) {
            var self = this;
            var invoiced = new $.Deferred();
            var pos = self.pos;

            if (!order.get_client()) {
                invoiced.reject({code: 400, message: 'Missing Customer', data: {}});
                return invoiced;
            }

            if (!order.get_client().email && order.get_quotation_type === 'send') {
                invoiced.reject({code: 400, message: 'Missing Customer Email', data: {}});
                return invoiced;
            }

            var order_id = pos.db.add_order(order.export_as_JSON());

            pos.flush_mutex.exec(function () {
                var done = new $.Deferred(); // holds the mutex

                var transfer = pos._flush_orders([pos.db.get_order(order_id)], {timeout: 30000, to_invoice: true});

                transfer.fail(function (error) {
                    invoiced.reject(error);
                    done.reject();
                });

                // on success, get the order id generated by the server
                transfer.pipe(function (order_server_id) {
                    pos.chrome.do_action(order_server_id);
                    invoiced.resolve();
                    done.resolve();
                });
                return done;

            });
            return invoiced;
        }
    });
    gui.define_popup({name: 'QuotationPopup', widget: QuotationPopupWidget});


});
