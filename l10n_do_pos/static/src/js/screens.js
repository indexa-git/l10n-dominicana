odoo.define('l10n_do_pos.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var rpc = require('web.rpc');
    var screens_return = require('pos_orders_history_return.screens');
    var core = require('web.core');
    var _t = core._t;

    screens.PaymentScreenWidget.include({

        customer_changed: function () {
            this._super.apply(this, arguments);
            var client = this.pos.get_client();
            var current_order = this.pos.get_order();
            if (client) {

                if (client.sale_fiscal_type_id &&
                    current_order.fiscal_type.prefix === 'B02') {
                    current_order.set_fiscal_type(
                        this.pos.get_fiscal_type_by_id(
                            client.sale_fiscal_type_id[0]
                        )
                    );
                }

            } else {
                current_order.set_fiscal_type(
                    this.pos.get_fiscal_type_by_prefix('B02')
                );
            }
        },

        renderElement: function () {
            this._super();
            var self = this;
            this.$('.js_set_fiscal_type').click(function () {
                self.click_set_fiscal_type();
            });
        },

        open_vat_popup: function () {
            var self = this;
            var current_order = self.pos.get_order();

            $('body').off('keypress', this.keyboard_handler);
            $('body').off('keydown', this.keyboard_keydown_handler);
            self.gui.show_popup('textinput', {
                'title': _t('You need to select a customer with RNC/Céd for' +
                    ' this fiscal type, place writes RNC/Céd'),
                'vat': '',
                confirm: function (vat) {
                    // That one comes from BarcodeEvents
                    $('body').keypress(this.keyboard_handler);
                    // That one comes from the pos, but we prefer to cover
                    // all the basis
                    $('body').keydown(this.keyboard_keydown_handler);
                    if (!(vat.length === 9 || vat.length === 11) ||
                        Number.isNaN(Number(vat))) {

                        self.gui.show_popup('error', {
                            'title': _t('This not RNC or Cédula'),
                            'body': _t('Please check if RNC or Cédula is' +
                                ' correct'),
                            cancel: function () {
                                self.open_vat_popup();
                            },
                        });

                    } else {
                        // TODO: in future try optimize search partners
                        // link get_partner_by_id
                        var partner = self.pos.partners.find(
                            function (partner_obj) {
                                return partner_obj.vat === vat;
                            }
                        );
                        if (partner) {
                            current_order.set_client(partner);
                        } else {
                            // TODO: in future create automatic partner
                            self.gui.show_screen('clientlist');
                        }
                    }

                },
                cancel: function () {
                    if (!current_order.get_client()) {
                        current_order.set_fiscal_type(
                            this.pos.get_fiscal_type_by_prefix('B02')
                        );
                    }
                    // That one comes from BarcodeEvents
                    $('body').keypress(this.keyboard_handler);
                    // That one comes from the pos, but we prefer to cover
                    // all the basis
                    $('body').keydown(this.keyboard_keydown_handler);
                },
            });
        },

        click_set_fiscal_type: function () {
            var self = this;

            var fiscal_type_list = _.map(self.pos.fiscal_types,
                function (fiscal_type) {
                    return {
                        label: fiscal_type.name,
                        item: fiscal_type,
                    };
                });

            self.gui.show_popup('selection', {
                title: _t('Select Fiscal Type'),
                list: fiscal_type_list,
                confirm: function (fiscal_type) {
                    var current_order = self.pos.get_order();
                    var client = self.pos.get_client();
                    current_order.set_fiscal_type(fiscal_type);
                    if (fiscal_type.required_document && !client) {
                        self.open_vat_popup();
                    }
                    if (fiscal_type.required_document && client) {
                        if (!client.vat) {
                            self.open_vat_popup();
                        }
                    }
                },
                is_selected: function (fiscal_type) {
                    return fiscal_type === self.pos.get_order().fiscal_type;
                },
            });
        },

        order_is_valid: function (force_validation) {

            var self = this;
            var current_order = this.pos.get_order();
            var client = current_order.get_client();
            var total = current_order.get_total_with_tax();
            var total_in_bank = 0;
            var has_cash = false;

            // TODO: var all_payment_lines = current_order.get_paymentlines();
            // TODO: for pass testing if (total === 0) {
            //     this.gui.show_popup('error', {
            //         'title': 'Sale in',
            //         'body': 'You cannot make sales in 0, please add a ' +
            //             'product with value',
            //     });
            //     return false;
            // }
            // for (var line in all_payment_lines) {
            //     var payment_line = all_payment_lines[line];
            //
            //     if (payment_line.cashregister.journal.type === 'bank') {
            //         total_in_bank =+ payment_line.amount;
            //     }
            //     if (payment_line.cashregister.journal.type === 'cash') {
            //         has_cash = true;
            //     }
            // }
            // if (Math.abs(Math.round(Math.abs(total) * 100) / 100) <
            //     Math.round(Math.abs(total_in_bank) * 100) / 100) {
            //
            //     this.gui.show_popup('error', {
            //         'title': 'Card payment',
            //         'body': 'Card payments cannot exceed the total order',
            //     });
            //
            //     return false;
            // }

            if (Math.round(Math.abs(total_in_bank) * 100) / 100 ===
                Math.round(Math.abs(total) * 100) / 100 && has_cash) {

                this.gui.show_popup('error', {
                    'title': 'Card and cash payment',
                    'body': 'The total payment with the card is sufficient ' +
                        'to pay the order, please eliminate the payment in ' +
                        'cash or reduce the amount to be paid by card',
                });

                return false;

            }

            if (self.pos.invoice_journal.fiscal_journal &&
                !current_order.to_invoice) {

                if (current_order.fiscal_type.required_document && !client) {

                    this.gui.show_popup('error', {
                        'title': 'Required document (RNC/Céd.)',
                        'body': 'For invoice fiscal type ' +
                            current_order.fiscal_type.name +
                            ' its necessary customer, please select customer',
                    });
                    return false;

                }

                if (client) {
                    if (current_order.fiscal_type.required_document &&
                        !client.vat) {

                        this.gui.show_popup('error', {
                            'title': 'Required document (RNC/Céd.)',
                            'body': 'For invoice fiscal type ' +
                                current_order.fiscal_type.name +
                                ' it is necessary for the customer have ' +
                                'RNC or Céd.',
                        });
                        return false;
                    }
                }

                if (current_order.fiscal_type.required_document && !client) {
                    this.gui.show_popup('error', {
                        'title': 'Required customer',
                        'body': 'For invoice fiscal type ' +
                            current_order.fiscal_type.name + ' it is ' +
                            'necessary customer, please select customer',
                    });
                    return false;
                }

                if (total >= 250000.00 && (!client || !client.vat)) {
                    this.gui.show_popup('error', {
                        'title': 'Sale greater than RD$ 250,000.00',
                        'body': 'For this sale it is necessary for the ' +
                            'customer have ID',
                    });
                    return false;
                }
            }
            return this._super(force_validation);

        },
        finalize_validation: function () {

            // TODO: for passing testing
            // var self = this;
            // var _super = this._super.bind(this);
            var current_order = this.pos.get_order();

            if (self.pos.invoice_journal.fiscal_journal &&
                !current_order.to_invoice) {

                console.log('im fiscal');
                
                // TODO: for passing testing
                // $('.freeze_screen').addClass("active_state");
                // $(".lds-spinner").show();
                // rpc.query({
                //     model: 'account.fiscal.type',
                //     method: 'get_next_fiscal_sequence',
                //     args: [
                //         [current_order.fiscal_type.id],
                //         [self.pos.company.id],
                //     ],
                // }).then(function (res) {
                //     current_order.ncf = res.ncf;
                //     current_order.fiscal_type_id =
                //         current_order.fiscal_type.id;
                //     current_order.ncf_expiration_date =
                //         res.ncf_expiration_date;
                //     current_order.fiscal_sequence_id =
                //         res.fiscal_sequence_id;
                //     console.log(res);
                //     }, function (type, err) {
                //         console.log(type);
                //         console.log(err);
                // }).done(function () {
                //     $('.freeze_screen').removeClass("active_state");
                //     $(".lds-spinner").hide();
                //     _super();
                // }).fail(function () {
                //     $('.freeze_screen').removeClass("active_state");
                //     $(".lds-spinner").hide();
                //     self.gui.show_popup('error', {
                //         'title': 'Error connection',
                //         'body': 'Please check your internet connection',
                //     });
                // });

            } else {
                this._super();
            }

        },
    });

    screens_return.OrdersHistoryScreenWidget.include({
        load_order_by_barcode: function (barcode) {
            var self = this;
            var _super = this._super.bind(this);
            if (self.pos.config.return_orders &&
                self.pos.invoice_journal.fiscal_journal) {

                var order_custom = false;
                var domain = [
                    ['ncf', '=', barcode],
                    ['returned_order', '=', false],
                ];
                var fields = [
                    'pos_history_reference_uid',
                ];
                rpc.query({
                    model: 'pos.order',
                    method: 'search_read',
                    args: [domain, fields],
                    limit: 1,
                }, {
                    timeout: 3000,
                    shadow: true,
                }).then(function (order) {
                    order_custom = order;
                }, function (err, event) {
                    event.preventDefault();
                    console.error(err);
                    self.gui.show_popup('error', {
                        'title': _t('Error: Could not find the Order'),
                        'body': err.data,
                    });
                }).done(function () {
                    if (order_custom && order_custom.length) {
                        _super(order_custom[0].pos_history_reference_uid);
                    } else {
                        self.gui.show_popup('error', {
                            'title': _t('Error: Could not find the Order'),
                            'body': _t('There is no order with this barcode.'),
                        });
                    }
                });
            } else {
                this._super(barcode);
            }
        },
    });
});
