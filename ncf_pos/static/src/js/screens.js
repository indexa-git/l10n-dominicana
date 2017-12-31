odoo.define('ncf_pos.screens', function(require) {
    "use strict";

    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var PopupWidget = require('point_of_sale.popups');

    var SuperOrder = models.Order;
    var QWeb = core.qweb;
    var _t = core._t;

    screens.ReceiptScreenWidget.include({

        ncf_render_receipt: function (fiscal_data, order) {
            console.log(fiscal_data, order);
            order.fiscal_type_name = fiscal_data.fiscal_type_name;
            order.ncf = fiscal_data.ncf;
            order.origin_ncf = fiscal_data.origin;
            if (!this.pos.config.iface_print_via_proxy) { // browser (html) printing
                this.$('.pos-receipt-container').html(QWeb.render('PosTicket', {
                    widget: this,
                    order: order,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines(),
                }));
            } else { // proxy (xml) printing
                var self = this;
                var env = {
                    widget:  this,
                    pos: this.pos,
                    order: order,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines()
                };
                var receipt = QWeb.render('XmlReceipt',env);
                this.pos.proxy.print_receipt(receipt);
                order._printed = true;
            }
        },
        render_receipt: function () {
            var self = this;
            var order = this.pos.get_order();
            if (!this.pos.config.iface_print_via_proxy) {
                $(".pos-sale-ticket").addClass('oe_hidden');
                $(".button.next.highlight").addClass('oe_hidden');
                $(".button.print").addClass('oe_hidden');
                rpc.query({
                    model: 'pos.order',
                    method: 'get_fiscal_data',
                    args: [{'order': order.name,}]}).then(function (fiscal_data) {
                    self.ncf_render_receipt(fiscal_data, order);
                    $(".pos-sale-ticket").removeClass('oe_hidden');
                    $(".button.next.highlight").removeClass('oe_hidden');
                    $(".button.print").removeClass('oe_hidden');
                });
            }
        },
        print_xml: function () {
            var self = this;
            var order = this.pos.get_order();
                if (this.pos.config.iface_print_via_proxy) {
                rpc.query({
                    model: 'pos.order',
                    method: 'get_fiscal_data',
                    args: [{'order': order.name,}]}).then(function (fiscal_data) {
                    self.ncf_render_receipt(fiscal_data, order);
                });
            }
        },
    });

    screens.ActionpadWidget.include({
        renderElement: function () {
            this._super();
            var self = this;

            this.$('.pay').bind("click", function () {
                var client = self.pos.get_order().get_client();

                if (client == null) {
                    alert("Debe seleccionar un cliente para poder realizar el Pago, o utilizar el Cliente por defecto; de no tener un cliente por defecto, pida ayuda a su Encargado para que lo establezca.");
                    return;
                }

                if ((client.sale_fiscal_type == 'fiscal' || client.sale_fiscal_type == 'gov' || client.sale_fiscal_type == 'special') && (client.vat == false || client.vat == null)) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Para el tipo de comprobante',
                        'body': 'No puede crear una factura con crédito fiscal si el cliente no tiene RNC o Cédula. Puede pedir ayuda para que el cliente sea registrado correctamente si este desea comprobante fiscal',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                }

                if (self.pos.get_order().orderlines.models.length == 0) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Factura sin productos',
                        'body': 'No puede pagar un ticket sin productos',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                }
            });
        }
    });

    screens.PaymentScreenWidget.include({

        validate_order: function (force_validation) {
            var currentOrder = this.pos.get_order();

            if (!currentOrder.get_client()) {
                this.gui.show_popup('error', {
                    'title': 'Debe establecer un cliente para completar la venta.',
                    'body': 'También se puede configurar un cliente por defecto en la confguracion del TPV.'
                });
                return;
            }

            else if (this.order_is_valid(force_validation)) {
                this.finalize_validation();
            }
        },

        click_paymentmethods: function (id) {
            var self = this;

            var cashregister = null;
            for (var i = 0; i < this.pos.cashregisters.length; i++) {
                if (this.pos.cashregisters[i].journal_id[0] == id) {
                    cashregister = this.pos.cashregisters[i];
                    break;
                }
            }
            var order = self.pos.get_order();

            if (cashregister.journal.type == "bank" && !cashregister.journal.credit) {
                self.gui.show_popup('payment_screen_text_input', {
                    title: "Digite un número de referencia",
                    confirm: function (input) {
                        cashregister.payment_reference = input;
                        self.pos.get_order().add_paymentline(cashregister);
                        self.reset_input();
                        self.render_paymentlines();
                    }
                });

            } else {
                this._super(id);
            }
        }
    });
});
