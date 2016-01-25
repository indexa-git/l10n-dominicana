odoo.define('pos_manager.chrome', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');
    var screens = require('point_of_sale.screens');

    chrome.Chrome.include({
        init: function () {
            this._super.apply(this, arguments);
            this.pos.bind('change:selectedOrder', this.check_allow_delete_order, this)
        },
        check_allow_delete_order: function () {
            var self = this;
            var cashier = self.pos.get_cashier();
            var order = this.pos.get_order();

            if (order.order_type === "refund") {
                this.refund_mode();
            } else {
                this.order_mode();
            }


            if (order.get_order_type() === "order") {
                //allow_delete_order
                if (!cashier.allow_delete_order) {
                    self.$('.deleteorder-button').toggle(order.is_empty());
                } else if (cashier.allow_delete_order) {
                    self.$('.deleteorder-button').show()
                }

                self.$(".button.pay").toggle(cashier.allow_payments);

                //allow_discount
                self.$el.find("[data-mode='discount']").css('visibility', 'visible');
                if (cashier.allow_discount === 0) {
                    self.$el.find("[data-mode='discount']").css('visibility', 'hidden')
                }

                //allow_edit_price
                self.$el.find("[data-mode='price']").css('visibility', 'visible');
                if (!cashier.allow_edit_price) {
                    self.$el.find("[data-mode='price']").css('visibility', 'hidden')
                }

                self.$el.find(".numpad-minus").css('visibility', 'visible');
                if (!cashier.allow_refund) {
                    self.$el.find(".numpad-minus").css('visibility', 'hidden')
                }

                self.$el.find(".refund-money-button").css('visibility', 'visible');
                if (!cashier.allow_cash_refund) {
                    self.$el.find(".refund-money-button").css('visibility', 'hidden')
                }
            }

        },

        loading_hide: function () {
            this._super();
            //extra checks on init
            this.check_allow_delete_order();
        },
        refund_mode: function () {
            $(".control-buttons").hide();
            $(".actionpad").hide();
            $(".numpad").hide();
            $(".searchbox").hide();
            $(".header-row").hide();
            $(".control-buttons-refund").show();
            $(".pos-rightheader").hide();
        },
        order_mode: function () {
            $(".control-buttons").show();
            $(".actionpad").show();
            $(".numpad").show();
            $(".searchbox").show();
            $(".header-row").show();
            $(".control-buttons-refund").hide();
            $(".pos-rightheader").show();

        }
    });

    chrome.OrderSelectorWidget.include({
        renderElement: function () {
            this._super();
            this.chrome.check_allow_delete_order();
        }
    });

    screens.OrderWidget.include({
        bind_order_events: function () {
            this._super();
            var order = this.pos.get('selectedOrder');
            order.orderlines.bind('add remove', this.chrome.check_allow_delete_order, this.chrome)
        }
    });

    screens.NumpadWidget.include({
        clickDeleteLastChar: function () {
            var self = this;
            var cashier = self.pos.get_cashier();

            var allow_delete_order_line = true;


            if (!cashier.allow_delete_order_line) {
                allow_delete_order_line = false
            }


            if (this.state.get('buffer') === "" && this.state.get('mode') === 'quantity' && !allow_delete_order_line) {
                return;
            }
            return this._super();
        }
    });

});
