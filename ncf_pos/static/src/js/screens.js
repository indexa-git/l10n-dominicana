odoo.define('ncf_pos.screens', function (require) {
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');
    var PopUpWidget = require('point_of_sale.popups');
    var form_common = require('web.form_common');

    var QWeb = core.qweb;
    var _t = core._t;


    screens.ReceiptScreenWidget.include({

        render_receipt: function () {
            var self = this;
            var order = this.pos.get_order();
            var client = order.attributes.client;

            new Model('pos.order').call("get_ncf", [order.name]).then(function (result) {

                var ncf = result.ncf;
                var fiscal_type = ncf.slice(9, 11);
                var invoice_type;
                switch (fiscal_type) {
                    case "01":
                        invoice_type = "FACTURA CON VALOR FISCAL";
                        break;
                    case "02":
                        invoice_type = "FACTURA PARA CONSUMIDOR FINAL";
                        break;
                    case "14":
                        invoice_type = "FACTURA GUBERNAMENTAL";
                        break;
                    case "15":
                        invoice_type = "FACTURA PARA REGIMENES ESPECIALES";
                        break;
                    default:
                        invoice_type = "NOTA DE CREDITO";
                }
                ;
                console.log(fiscal_type);
                self.$('.pos-receipt-container').html(QWeb.render('PosTicket', {
                    widget: self,
                    order: order,
                    invoice_type: invoice_type,
                    ncf: ncf,
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
            // return this.pos.loyalty && this.pos.loyalty.rewards.length;
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

            this.$("#quotation_cancel").click(function(){
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
                    // generate the pdf and download it
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
