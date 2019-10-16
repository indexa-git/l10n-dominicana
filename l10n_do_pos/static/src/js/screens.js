odoo.define('l10n_do_pos.screens', function(require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var rpc = require('web.rpc');

    // var core = require('web.core');
    // var screens_history = require('pos_orders_history.screens');
    // var screens_return = require('pos_orders_history_return.screens')
    // var Model = require('web.Model');
    // var _t = core._t;

    screens.PaymentScreenWidget.include({

        customer_changed: function () {
            this._super.apply(this, arguments);
            var client = this.pos.get_client();
            var current_order = this.pos.get_order();
            if(client){

                if(client.sale_fiscal_type_id && current_order.fiscal_type.prefix === 'B02'){
                    current_order.set_fiscal_type(this.pos.get_fiscal_type(client.sale_fiscal_type_id[0]));
                }
            }else{
                current_order.set_fiscal_type(current_order.get_consumo());
            }
        },

        renderElement: function () {
            this._super();
            var self = this;
            this.$('.js_set_fiscal_type').click(function(){
                self.click_set_fiscal_type();
            });
        },

        open_vat_popup(){
            var self = this;
            var current_order = self.pos.get_order();

            // self.gui.show_popup('confirm',{
            //     'title': _t('Please select the Customer'),
            //     'body': _t('You need to select a customer with RNC/Céd for this fiscal type'),
            //     confirm: function(){
            //         self.gui.show_screen('clientlist');
            //     },
            // });
            $('body').off('keypress', this.keyboard_handler);
            $('body').off('keydown', this.keyboard_keydown_handler);
            self.gui.show_popup('textinput', {
                'title': _t('You need to select a customer with RNC/Céd for this fiscal type, place writes RNC/Céd'),
                'vat': '',
                confirm: function(vat) {
                    // that one comes from BarcodeEvents
                    $('body').keypress(this.keyboard_handler);
                    // that one comes from the pos, but we prefer to cover all the basis
                    $('body').keydown(this.keyboard_keydown_handler);
                    if(!(vat.length === 9 || vat.length === 11) || Number.isNaN(Number(vat))){
                        self.gui.show_popup('error', {
                            'title':_t('This not RNC or Cédula'),
                            'body': _t('Please check if RNC or Cédula is correct'),
                            cancel: function () {
                                self.open_vat_popup()
                            }
                        });
                    }else{
                        //TODO: in future try optimize seatch partners linke get_partner_by_id
                        var partner = self.pos.partners.find(partner => partner.vat === vat);
                        if(partner){
                            current_order.set_client(partner)
                        }else{
                            //TODO: in future create automatic partner
                            self.gui.show_screen('clientlist')
                        }
                    }

                },
                cancel: function () {
                    if(!current_order.get_client()){
                        current_order.set_fiscal_type(current_order.get_consumo())
                    }
                    // that one comes from BarcodeEvents
                    $('body').keypress(this.keyboard_handler);
                    // that one comes from the pos, but we prefer to cover all the basis
                    $('body').keydown(this.keyboard_keydown_handler);
                }
            });
        },

        click_set_fiscal_type: function () {
            var self = this;

            var fiscal_type_list = _.map(self.pos.fiscal_types, function (fiscal_type) {
                return {
                    label: fiscal_type.name,
                    item: fiscal_type
                };
            });

            self.gui.show_popup('selection', {
                title: _t('Select Fiscal Type'),
                list: fiscal_type_list,
                confirm: function (fiscal_type) {
                    var current_order = self.pos.get_order();
                    var client  = self.pos.get_client();
                    current_order.set_fiscal_type(fiscal_type);
                    if(fiscal_type.required_document && !client){
                        self.open_vat_popup()
                    }
                    if(fiscal_type.required_document && client){
                        if(!client.vat){
                            self.open_vat_popup()
                        }
                    }
                },
                is_selected: function (fiscal_type) {
                    return fiscal_type === self.pos.get_order().fiscal_type;
                }
            });
        },

        order_is_valid: function (force_validation){

            var self = this;
            var current_order = this.pos.get_order();
            var client = current_order.get_client();
            var total = current_order.get_total_with_tax();
            var all_payment_lines = current_order.get_paymentlines();
            var sale_fiscal_sequence = null;
            var total_in_bank = 0;
            var has_cash = false;

            // if (total == 0) {
            //     this.gui.show_popup('error', {
            //         'title': 'Sale in',
            //         'body': 'You cannot make sales in 0, please add a product with value'
            //     });
            //     return false
            // }

            for (var line in all_payment_lines){
                var payment_line = all_payment_lines[line];

                if (payment_line.cashregister.journal.type == 'bank'){
                    total_in_bank =+ payment_line.amount
                }
                if(payment_line.cashregister.journal.type == 'cash'){
                    has_cash = true
                }

            }

            if (Math.abs(Math.round(Math.abs(total) * 100) / 100) < Math.round(Math.abs(total_in_bank) * 100) / 100 ) {
                this.gui.show_popup('error', {
                    'title': 'Card payment',
                    'body': 'Card payments cannot exceed the total order'
                });
                return false;
            }

            if (Math.round(Math.abs(total_in_bank) * 100) / 100 == Math.round(Math.abs(total) * 100) / 100 && has_cash) {
                this.gui.show_popup('error', {
                    'title': 'Card and cash payment',
                    'body': 'The total payment with the card is sufficient to pay the order, please eliminate the payment in cash or reduce the amount to be paid by card'
                });
                return false;
            }
            if(self.pos.invoice_journal.fiscal_journal){
                // if(current_order.get_mode() === 'return'){
                //
                //     sale_fiscal_sequence = self.pos.db.get_sale_fiscal_sequence('credit_note');
                //
                //     if(!client){
                //         client = self.pos.db.get_partner_by_id(self.pos.config.default_partner_id[0])
                //     }
                //
                //     var origin_order = self.pos.db.orders_history_by_id[current_order.return_lines[0].order_id[0]];
                //
                //     if ( all_payment_lines.length != 0 ){
                //         this.gui.show_popup('error', {
                //             'title': 'Error en Nota de Crédito',
                //             'body': 'Las Notas de Crédito no pueden tener pagos asignados, favor borrar todos los pagos.'
                //         });
                //         return false
                //     }
                //
                //     if (origin_order.partner_id[0] != client.id){
                //         this.gui.show_popup('error', {
                //             'title': 'Error en Nota de Crédito',
                //             'body': 'El cliente debe ser el mismo que la orden original.'
                //         });
                //         return false
                //     }
                //
                // }else{

                    if (current_order.fiscal_type.required_document && !client) {
                        this.gui.show_popup('error', {
                            'title': 'Required document (RNC/Céd.)',
                            'body': 'For invoice fiscal type ' + current_order.fiscal_type.name + ' its necessary customer, please select customer'
                        });
                        return false
                    }

                    if(client){
                        if (current_order.fiscal_type.required_document && !client.vat) {
                            this.gui.show_popup('error', {
                                'title': 'Required document (RNC/Céd.)',
                                'body': 'For invoice fiscal type ' + current_order.fiscal_type.name + ' it is necessary for the customer have RNC or Céd.'
                            });
                            return false
                        }
                    }

                    if (current_order.fiscal_type.required_document && !client) {
                        this.gui.show_popup('error', {
                            'title': 'Required customer',
                            'body': 'For invoice fiscal type ' + current_order.fiscal_type.name + ' it is necessary customer, please select customer'
                        });
                        return false
                    }

                    if (total >= 250000.00 && (!client || !client.vat)) {
                        this.gui.show_popup('error', {
                            'title': 'Sale greater than RD$ 250,000.00',
                            'body': 'For this sale it is necessary for the customer have ID'
                        });
                        return false
                    }

                    // //for payment with credit note
                    // var has_return_move_name = true;
                    // var payment_and_return_mount_equals = true;
                    //
                    // all_payment_lines.forEach(function (payment_line) {
                    //     if(payment_line.cashregister.journal.is_for_credit_notes){
                    //
                    //         if(payment_line.get_returned_move_name() === null){
                    //             has_return_move_name = false;
                    //         }
                    //
                    //         var amount_in_payment_line = Math.round(payment_line.amount*100)/100;
                    //         var amount_in_return_order = Math.abs(payment_line.get_returned_order_amount()*100)/100;
                    //
                    //         if(amount_in_return_order != amount_in_payment_line){
                    //             payment_and_return_mount_equals = false;
                    //         }
                    //     };
                    // });
                    //
                    // if(!has_return_move_name){
                    //     this.gui.show_popup('error', {
                    //         'title': 'Error en pago con nota de crédito',
                    //         'body': 'Existe un error con el pago de nota de crédito, favor borrar el pago de la nota de crédito y escanearlo nuevamente.'
                    //     });
                    //
                    //     return false
                    // }

                    // if(!payment_and_return_mount_equals){
                    //     this.gui.show_popup('error', {
                    //         'title': 'Error en pago con nota de crédito',
                    //         'body': 'Existe un error con el monto de nota de crédito, favor borrar el pago de la nota de crédito y escanearlo nuevamente.'
                    //     });
                    //
                    //     return false
                    // }


                // }


                // if (!sale_fiscal_sequence.is_ncf_active) {
                //     this.gui.show_popup('error', {
                //         'title': 'Comprobante inactivo',
                //         'body': 'El comprobante '+ sale_fiscal_sequence.name+' esta inactivo, favor contactar con el encargado de contabilidad para activarlo en la configuración del diario '+ self.pos.config.invoice_journal_id[1]
                //     });
                //     return false
                //
                // }

                // if (sale_fiscal_sequence.ncf_max < sale_fiscal_sequence.number_next_actual) {
                //     this.gui.show_popup('error', {
                //         'title': 'Secuencia agotada',
                //         'body': 'El comprobante '+ sale_fiscal_sequence.name +' alcanzó su número máximo, favor contactar con el encargado de contabilidad para actualizar el nuevo número máximo en la configuración del diario '+ self.pos.config.invoice_journal_id[1]
                //     });
                //     return false
                //
                // }

                // if (new Date(sale_fiscal_sequence.ncf_expiration_date) < new Date(Date.now())) {
                //     this.gui.show_popup('error', {
                //         'title': 'Secuencia expirada',
                //         'body': 'La secuencia de '+ sale_fiscal_sequence.name +' esta expirada, favor contactar con el encargado de contabilidad para actualizar la nueva fecha de expiración en la configuración del diario '+ self.pos.config.invoice_journal_id[1]
                //     });
                //     return false
                // }

            }
            return this._super(force_validation);

        },
        finalize_validation: function () {

            var self = this;
            var current_order = this.pos.get_order();
            var _super = this._super.bind(this);

            //TODO: this part is for return order (credit note)
            // if(current_order.get_mode()=='return'){
            //
            //     sale_fiscal_sequence = self.pos.db.get_sale_fiscal_sequence('credit_note');
            //     var origin_order = self.pos.db.orders_history_by_id[current_order.return_lines[0].order_id[0]];
            //     current_order.origin_move_name = origin_order.move_name;
            //
            // }

            if(self.pos.invoice_journal.fiscal_journal){
                rpc.query({
                    model: 'account.fiscal.type',
                    method: 'get_next_fiscal_sequence',
                    args: [[current_order.fiscal_type.id],[self.pos.company.id]],
                })
                .then(function (res){
                    current_order.ncf = res.ncf;
                    current_order.fiscal_type_id = current_order.fiscal_type.id;
                    current_order.ncf_expiration_date = res.ncf_expiration_date;
                    current_order.fiscal_sequence_id = res.fiscal_sequence_id;
                    console.log(res)
                }, function(type,err) {
                    console.log(type);
                    console.log(err)
                }).done(function () {

                    _super()

                }).fail(function () {
                    console.log('fail')
                })

            }else{
                this._super()
            }

        },

        //for return norder

        // show: function(){
        //     this._super();
        //     this.disable_customer_button();
        // },
        //
        // disable_customer_button: function() {
        //     var order = this.pos.get_order();
        //
        //     if (order.get_mode() != 'return') {
        //         this.$('.js_set_customer').removeClass('disable');
        //     } else {
        //         this.$('.js_set_customer').addClass('disable');
        //     }
        // },

    //     click_paymentmethods: function (id) {
    //         var self = this;
    //         var cashregister = null;
    //         for (var i = 0; i < this.pos.cashregisters.length; i++) {
    //             if (this.pos.cashregisters[i].journal_id[0] === id) {
    //                 cashregister = this.pos.cashregisters[i];
    //                 break;
    //             }
    //         }
    //         var current_order = self.pos.get_order();
    //
    //
    //         if (cashregister.journal.is_for_credit_notes == true) {
    //
    //             self.gui.show_popup('textinputpaymentscreen', {
    //                 title: "Digite el NCF de la nota de crédito",
    //                 confirm: function (input) {
    //                     console.log(input);
    //                     current_order.add_payment_credit_note(input, cashregister)
    //                 }
    //             })
    //         } else {
    //             this._super(id);
    //         }
    //     }
    //
    });

    // screens.ActionpadWidget.include({
    //     renderElement: function () {
    //         this._super();
    //         this.disable_customer_button();
    //     },
    //
    //     disable_customer_button: function() {
    //         var order = this.pos.get_order();
    //
    //         if (order.get_mode() != 'return') {
    //             this.$('.set-customer').removeClass('disable');
    //         } else {
    //             this.$('.set-customer').addClass('disable');
    //         }
    //     },
    //
    // });

    // screens.ClientListScreenWidget.include({
    //
    //     show: function(){
    //         this._super();
    //         var self = this;
    //         this.$('.new-customer').click(function(){
    //             self.display_client_details('edit',{
    //                 'sale_fiscal_type': 'consumo',
    //             });
    //         });
    //     },
    // });

    // screens.ReceiptScreenWidget.include({
    //     render_receipt: function() {
    //         this._super();
    //
    //         // if (this.pos.config.show_barcode_in_receipt) {
    //         var order = this.pos.get_order();
    //         var receipt_reference = order.move_name;
    //         if (order.move_name){
    //             this.$el.find('#barcode').JsBarcode(receipt_reference, {format: "code128"});
    //             this.$el.find('#barcode').css({
    //                 "width": "100%"
    //             });
    //         }
    //         // }
    //     },

        //TODO: esta parte es para usar con el posbox

        // print_xml: function() {
        //     if (this.pos.config.show_barcode_in_receipt) {
        //         var env = {
        //             widget:  this,
        //             pos: this.pos,
        //             order: this.pos.get_order(),
        //             receipt: this.pos.get_order().export_for_printing(),
        //             paymentlines: this.pos.get_order().get_paymentlines()
        //         };
        //         var receipt = QWeb.render('XmlReceipt',env);
        //         var barcode = this.$el.find('#barcode').parent().html();
        //         receipt = receipt.split('<img id="barcode"/>');
        //         receipt[0] = receipt[0] + barcode + '</img>';
        //         receipt = receipt.join('');
        //         this.pos.proxy.print_receipt(receipt);
        //         this.pos.get_order()._printed = true;
        //     } else {
        //         this._super();
        //     }
        // },
    // });

    // screens.ScreenWidget.include({
    //     barcode_product_action: function(code) {
    //         var self = this;
    //         var screen_name = this.gui.get_current_screen();
    //
    //         var order = this.pos.db.get_sorted_orders_history(1000).find(function(o) {
    //             var move_name = o.move_name;
    //             return move_name === code.code
    //         });
    //         if (screen_name === "orders_history_screen") {
    //             console.log(code.code)
    //             if (order) {
    //                 this.gui.current_screen.search_order_on_history(order);
    //                 return;
    //             }
    //             var popup = this.pos.gui.current_popup;
    //             if (popup && popup.options.barcode) {
    //                 popup.$('input,textarea').val(code.code);
    //                 popup.click_confirm();
    //             } else {
    //                 this.gui.show_popup('error',{
    //                     'title': _t('Error: Could not find the Order'),
    //                     'body': _t('There is no order with this barcode.')
    //                 });
    //             }
    //         }else if (screen_name === "payment") {
    //
    //             var current_order = self.pos.get_order();
    //             var cashregister = null;
    //
    //             for (var i = 0; i < this.pos.cashregisters.length; i++) {
    //
    //                 if (this.pos.cashregisters[i].journal.is_for_credit_notes === true) {
    //                     cashregister = this.pos.cashregisters[i];
    //                     break;
    //                 }
    //
    //             }
    //             if(cashregister === null){
    //                 self.gui.show_popup('error', {
    //                     'title': 'Método de pago no existe',
    //                     'body': 'El metodo de pago de nota de crédito no existe, favor configurarlo'
    //                 });
    //             }else{
    //                 current_order.add_payment_credit_note(code.code, cashregister);
    //             }
    //
    //
    //
    //         }else {
    //             this._super(code);
    //         }
    //     },
    //     // // what happens when a barcode is scanned :
    //     // // it will add the order reference to the search in orders history screen
    //     // search_order_on_history: function(order) {
    //     //     this.gui.current_screen.$('.searchbox input').val(order.pos_reference);
    //     //     this.gui.current_screen.$('.searchbox input').keypress();
    //     // },
    // });


    // screens_history.OrdersHistoryScreenWidget.include({
    //     show: function(){
    //         var self = this;
    //         this._super();
    //
    //         this.$('.searchboxg input').on('keypress',function (event) {
    //             clearTimeout(search_timeout);
    //
    //             var query = this.value;
    //
    //             search_timeout = setTimeout(function () {
    //                 self.perform_search(query,event.which === 13);
    //             },70);
    //         });
    //
    //     },
    //
    // });

    // screens_return.OrdersHistoryScreenWidget.include({
    //     load_order_by_barcode: function(barcode) {
    //         console.log(barcode)
    //         if (this.pos.config.return_orders) {
    //             var self = this;
    //             new Model('pos.order').call('search_read', [[['move_name', '=', barcode], ['returned_order','=', false]]]).then(function(order) {
    //                 console.log(order)
    //                 if (order && order.length) {
    //                     new Model('pos.order').call('search_read', [[['pos_history_reference_uid', '=', order[0].pos_history_reference_uid]]]).then(function (o) {
    //                         console.log(o);
    //                         if (o && o.length) {
    //                             self.pos.update_orders_history(o);
    //                             o.forEach(function (exist_order) {
    //                                 self.pos.get_order_history_lines_by_order_id(exist_order.id).done(function (lines) {
    //                                     self.pos.update_orders_history_lines(lines);
    //                                     if (!exist_order.returned_order) {
    //                                         self.search_order_on_history(exist_order);
    //                                     }
    //                                 });
    //                             });
    //                         } else {
    //                             self.gui.show_popup('error', {
    //                                 'title': _t('Error: No se encontro la orden'),
    //                                 'body': _t('No existe una orden con este NCF (' + barcode + ').')
    //                             });
    //                         }
    //                     }, function (err, event) {
    //                         event.preventDefault();
    //                         console.error(err);
    //                         self.gui.show_popup('error', {
    //                             'title': _t('Error: Could not find the Order'),
    //                             'body': err.data,
    //                         });
    //                     });
    //                 }else {
    //                     self.gui.show_popup('error', {
    //                         'title': _t('Error: No se encontro la orden'),
    //                         'body': _t('No existe una orden con este NCF (' + barcode + ').')
    //                     });
    //                 }
    //             }, function (err, event) {
    //                 event.preventDefault();
    //                 console.error(err);
    //                 self.gui.show_popup('error', {
    //                     'title': _t('Error: Could not find the Order'),
    //                     'body': err.data,
    //                 });
    //             });
    //         } else {
    //             this._super(barcode);
    //         }
    //     },
    // });

});
