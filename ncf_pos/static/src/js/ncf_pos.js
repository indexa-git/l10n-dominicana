odoo.define('ncf_pos.ncf_ticket', function(require) {
    var core = require('web.core');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var Model = require('web.DataModel');
    var gui = require('point_of_sale.gui');

    var SuperOrder = models.Order;
    var QWeb = core.qweb;
    var _t = core._t;

    models.load_fields('pos.config', ['default_partner_id']);
    models.load_fields('res.partner', ['sale_fiscal_type']);
    models.load_fields('res.company', ['street', 'street2', 'city', 'state_id', 'country_id', 'zip']);

    models.load_models([{
        model: 'res.partner',
        fields: ['partner_id', 'sale_fiscal_type'],
        loaded: function (self) {
            self.sale_fiscal_type = [
                {"code": "final", "name": "Final"},
                {"code": "fiscal", "name": "Fiscal"},
                {"code": "gov", "name": "Gubernamental"},
                {"code": "special", "name": "Especiales"}];
        },
    }]);

    function space_pad(num,size){
        var s = ""+num;
        while (s.length < size) {
            s = s + " ";
        }
        return s;
    }

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        generate_wrapped_orderline_product_name: function() {

            //For Order line product name wrapped
            var MAX_LENGTH = 17; // 40 * line ratio of .6
            var wrapped = [];
            var name = this.get_product().display_name;
            var current_line = "";

            while (name.length > 0) {
                var space_index = 16;//name.indexOf(" ");

                if (space_index === -1) {
                    space_index = name.length;
                }

                if (current_line.length + space_index > MAX_LENGTH) {
                    if (current_line.length) {
                        wrapped.push(current_line);
                    }
                    current_line = "";
                }

                current_line += name.slice(0, space_index + 1);
                name = name.slice(space_index + 1);
            }

            if (current_line.length) {
                wrapped.push(current_line);
            }

          //For product comment wrapped
            if(this.pos.config.on_product_line){
                if(this.get_order_line_comment() && this.get_order_line_comment().length > 0){
                    var order_line_comment = this.get_order_line_comment();
                    var current_order_line_comment = "";

                    while (order_line_comment.length > 0) {
                        var comment_space_index = 16;//name.indexOf(" ");

                        if (comment_space_index === -1) {
                            comment_space_index = order_line_comment.length;
                        }

                        if (current_order_line_comment.length + comment_space_index > MAX_LENGTH) {
                            if (current_order_line_comment.length) {
                                wrapped.push(current_order_line_comment);
                            }
                            current_order_line_comment = "";
                        }

                        current_order_line_comment += order_line_comment.slice(0, comment_space_index + 1);
                        order_line_comment = order_line_comment.slice(comment_space_index + 1);
                    }

                    if (current_order_line_comment.length) {
                        wrapped.push(current_order_line_comment);
                    }
                }
            }

           //For Discount wrapped
            if(this.get_discount() > 0){
                var discount_name = "With a " + this.get_discount().toString()+" % discount";
                var current_discount_line = "";

                while (discount_name.length > 0) {
                    var discount_space_index = 16;//name.indexOf(" ");

                    if (discount_space_index === -1) {
                        discount_space_index = discount_name.length;
                    }

                    if (current_discount_line.length + discount_space_index > MAX_LENGTH) {
                        if (current_discount_line.length) {
                            wrapped.push(current_discount_line);
                        }
                        current_discount_line = "";
                    }

                    current_discount_line += discount_name.slice(0, discount_space_index + 1);
                    discount_name = discount_name.slice(discount_space_index + 1);
                }

                if (current_discount_line.length) {
                    wrapped.push(current_discount_line);
                }
            }
            return wrapped;
        },
        generate_wrapped_quantity_str: function(string_name) {
            var MAX_LENGTH = 5; // 40 * line ratio of .6
            var wrapped = [];
            var name = this.get_quantity_str_with_unit();
            var current_line = "";

            while (name.length > 0) {
                var space_index = 4;//name.indexOf(" ");

                if (space_index === -1) {
                    space_index = name.length;
                }

                if (current_line.length + space_index > MAX_LENGTH) {
                    if (current_line.length) {
                        current_line = space_pad(current_line,5)
                        wrapped.push(current_line);
                    }
                    current_line = "";
                }

                current_line += name.slice(0, space_index + 1);
                name = name.slice(space_index + 1);
            }

            if (current_line.length) {
                current_line = space_pad(current_line,5)
                wrapped.push(current_line);
            }

            return wrapped;
        },
    });

    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            SuperOrder.prototype.initialize.call(this, attributes, options);
            var self = this;
            if (!self.get_client()) {
                var default_partner_id = self.pos.db.get_partner_by_id(self.pos.config.default_partner_id[0]);
                self.set_client(default_partner_id);
            }
        },
    });

    screens.ReceiptScreenWidget.include({

        ncf_render_receipt: function(fiscal_data) {
            var order = this.pos.get_order();
            order.fiscal_type_name = fiscal_data.fiscal_type_name;
            order.ncf = fiscal_data.ncf;
            order.origin_ncf = fiscal_data.origin;
            this.$('.pos-receipt-container').html(QWeb.render('PosTicket', {
                widget: this,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
            }));
        },
        render_receipt: function() {
            var self = this;
            var order = this.pos.get_order();
            $(".pos-sale-ticket").hide();
            $(".button.next.highlight").hide();
            $(".button.print").hide();

            new Model('pos.order').call("get_fiscal_data", [order.name]).then(function(fiscal_data) {
                self.ncf_render_receipt(fiscal_data);
                $(".pos-sale-ticket").show();
                $(".button.next.highlight").show();
                $(".button.print").show();
            });
        },

        print_xml: function() {
            var env = {
                widget: this,
                pos: this.pos,
                order: this.pos.get_order(),
                receipt: this.pos.get_order().export_for_printing(),
                orderlines: this.pos.get_order().get_orderlines(),
                paymentlines: this.pos.get_order().get_paymentlines()
            };
            var receipt = QWeb.render('XmlReceipt', env);

            this.pos.proxy.print_receipt(receipt);
            this.pos.get_order()._printed = true;
        },

    });

    screens.PaymentScreenWidget.include({
        validate_client: function() {
            var order = this.pos.get_order();
            var client = order.get_client();

            if (!client) {
                return "¡Debe seleccionar un cliente para validar la venta!";
            }

            if (client.sale_fiscal_type !== 'final' && (client.vat === false || client.vat === null)) {
                self.gui.show_popup('error', {
                    'title': 'Error: Para el tipo de comprobante',
                    'body': 'No puede crear una factura con crédito fiscal si el cliente no tiene RNC o Cédula. Puede pedir ayuda para que el cliente sea registrado correctamente si este desea comprobante fiscal',
                    'cancel': function () {
                        self.gui.show_screen('products');
                    }
                });
            } else {

            return true;
            }
        },

        validate_order: function(force_validation) {
            var self = this;
            var res = self.validate_client();

            if (res !== true) {
                self.gui.show_popup('confirm', {
                    title: _t('Por favor corrija estos los datos'),
                    body:  _t(res),
                    confirm: function() {
                        self.gui.close_popup();
                    }
                });
            } else {
                if (res) {
                    if (this.order_is_valid(force_validation)) {
                        this.finalize_validation();
                        }
                }
            }
        },
    });

    var PaymentScreenTextInput = PopupWidget.extend({
        template: 'PaymentScreenTextInput',
        show: function (options) {
            window.document.body.removeEventListener('keypress', this.gui.current_screen.keyboard_handler);
            window.document.body.removeEventListener('keydown', this.gui.current_screen.keyboard_keydown_handler);
            options = options || {};
            this._super(options);

            this.renderElement();
            this.$('input,textarea').focus();

        },
        click_cancel: function () {
            window.document.body.addEventListener('keypress', this.gui.current_screen.keyboard_handler);
            window.document.body.addEventListener('keydown', this.gui.current_screen.keyboard_keydown_handler);
            this.gui.close_popup();
            if (this.options.cancel) {
                this.options.cancel.call(this);
            }
        },
        click_confirm: function () {
            window.document.body.addEventListener('keypress', this.gui.current_screen.keyboard_handler);
            window.document.body.addEventListener('keydown', this.gui.current_screen.keyboard_keydown_handler);
            var value = this.$('input,textarea').val();
            this.gui.close_popup();
            if (this.options.confirm) {
                this.options.confirm.call(this, value);
            }
        }
    });

    gui.define_popup({name: 'payment_screen_text_input', widget: PaymentScreenTextInput});

});
