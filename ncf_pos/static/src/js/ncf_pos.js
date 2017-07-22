odoo.define('ncf_pos.ncf_ticket', function(require) {
    "use strict";

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
        }
    });

    screens.PaymentScreenWidget.include({
        validate_client: function() {
            var order = this.pos.get_order();
            var client = order.get_client();

            if (!client) {
                return "¡Debe seleccionar un cliente para validar la venta!";
            }

            if (client.sale_fiscal_type == 'fiscal' && !client.vat) {
                return "El cliente seleccionado requiere RNC/Cédula. Acceda al cliente y agregue esta información";
            }

            if (client.sale_fiscal_type != 'fiscal' && client.vat) {
                return "El cliente seleccionado tiene RNC/Cédula, no puede entregar una factura sin VALOR FISCAL. Acceda al cliente y cambie el tipo de comprobante o remueva el RNC/Cédula";
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

});
