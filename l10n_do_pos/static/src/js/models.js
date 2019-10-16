odoo.define('l10n_do_pos.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var _super_order = models.Order.prototype;
    // var Model = require('web.Model');

    models.load_fields('res.partner', ['sale_fiscal_type_id']);
    // models.load_fields('account.journal', ['is_for_credit_notes']);

    models.load_models({
        model:  'account.journal',
        fields: ['name', 'fiscal_journal'],
        domain: function(self){
            return [['id', '=', self.config.invoice_journal_id[0]]];
        },
        loaded: function(self, journals){
            self.invoice_journal = false;
            if(journals[0]){
                self.invoice_journal = journals[0];
            }
        },
    });

    models.load_models({
        model:  'account.fiscal.sequence',
        fields: ['name', 'fiscal_type_id'],
        domain: function(self){
            return [['state', '=', 'active'],['type', '=', 'sale'], ['company_id', '=', self.company.id]];
        },
        loaded: function(self, fiscal_sequences){
            self.fiscal_sequences = fiscal_sequences

        },
    });

    models.load_models({
        model:  'account.fiscal.type',
        fields: ['name', 'fiscal_position_id', 'required_document', 'prefix', 'internal_generate'],
        domain: function(self){
            return [['type', '=', 'sale']];
        },
        loaded: function(self, fiscal_types){
            self.fiscal_types = fiscal_types
        },
    });

    //TODO: this part is for offline mode

    // models.load_models({
    //     model:  'account.fiscal.sequence',
    //     fields: ['name', 'is_ncf_active', 'ncf_expiration_date', 'number_next_actual', 'ncf_max', 'sale_fiscal_type',  'ncf_journal_id', 'sale_fiscal_type_name', 'prefix', 'padding'],
    //     domain: function(self){
    //
    //         return [['state', '=', 'active']];
    //
    //     },
    //     loaded: function(self, sequences){
    //
    //         if(self.db.cache.orders === undefined || self.db.cache.orders.length == 0){
    //
    //             self.db.all_sale_fiscal_sequence = sequences;
    //             self.db.sale_fiscal_sequences_by_id = {};
    //
    //             sequences.forEach(function(sequence) {
    //                 self.db.sale_fiscal_sequences_by_id[sequence.sale_fiscal_type] = sequence;
    //             });
    //
    //             console.log('Sequencias acutalizadas');
    //             console.log(sequences);
    //
    //         }else{
    //
    //             self.db.all_sale_fiscal_sequence = self.db.load('all_sale_fiscal_sequence');
    //             self.db.sale_fiscal_sequences_by_id = self.db.load('sale_fiscal_sequences_by_id');
    //             console.log('secuencias usadas de la memoria cache');
    //             console.log( self.db );
    //
    //
    //         }
    //
    //     },
    // });

    models.Order = models.Order.extend({
        initialize: function () {
            _super_order.initialize.apply(this,arguments);

            var self = this;
			this.ncf = '';
			this.ncf_origin_out = '';
			this.ncf_expiration_date = '';
			this.fiscal_type = false;
			this.fiscal_type_id = false;
			this.fiscal_sequence_id = false;
			var client = self.get_client();
			if(client){
			    if(client.sale_fiscal_type_id){
			        self.fiscal_type = self.pos.get_fiscal_type(client.sale_fiscal_type_id[0]);
                }else{
			        self.fiscal_type = self.get_consumo();
                }
            }else{
			    self.fiscal_type = self.get_consumo();
            }
            this.save_to_db();
        },

        get_consumo: function(){
            //TODO: try optimize this part
            var self = this;
            var consumo = false;
            self.pos.fiscal_types.forEach(function (fiscal_type) {
                if(fiscal_type.prefix === 'B02'){
                    consumo = fiscal_type
                }
            });

            if(consumo){
                return consumo
            }else{
                self.pos.gui.show_popup('error', {
                    'title':_t('Fiscal type not found'),
                    'body': _t('Default fiscal type not exist'),
                });
                return false
            }
        },

        set_fiscal_type: function (fiscal_type) {
            this.fiscal_type = fiscal_type;
            this.fiscal_type_changed()
        },
        get_fiscal_type: function () {
            return this.fiscal_type
        },
        fiscal_type_changed: function () {
            var current_order = this.pos.get_order();
            var fiscal_type_name = current_order.fiscal_type.name || false;
            this.pos.gui.screen_instances.payment.$('.js_fiscal_type_name').text(
                fiscal_type_name
            );
            this.pos.gui.screen_instances.products.$('.js_fiscal_type_name').text(
                fiscal_type_name
            )
        },


        export_as_JSON: function() {

			var self = this;
			var loaded = _super_order.export_as_JSON.call(this);
			var current_order = self.pos.get_order();

			if(self.pos.get_order()){
			    loaded.ncf = current_order.ncf;
			    loaded.ncf_origin_out = current_order.ncf_origin_out;
			    loaded.ncf_expiration_date = current_order.ncf_expiration_date;
                loaded.fiscal_type_id = current_order.fiscal_type_id;
                loaded.fiscal_sequence_id = current_order.fiscal_sequence_id;
            }

			return loaded;

		},

        //TODO: this part is for credit note

        // add_payment_credit_note: function (credit_note_ncf, cashregister) {
        //     var self = this;
        //     var payment_lines = self.get_paymentlines();
        //     var is_on_payment_line = false;
        //
        //     payment_lines.forEach(function(payment_line) {
        //           if(payment_line.get_returned_move_name() != null){
        //               if(payment_line.get_returned_move_name() === credit_note_ncf){
        //                   is_on_payment_line = true
        //               }
        //           }
        //     });
        //
        //     if(is_on_payment_line){
        //         self.pos.gui.show_popup('error', {
        //             'title': 'Nota de crédito Registrada',
        //             'body': 'Esta nota de crédito '+ credit_note_ncf +' ya esta en la orden de venta, favor intentarlo nuevamente'
        //         });
        //
        //         return false
        //
        //     }else{
        //
        //         $('.freeze_screen').addClass("active_state");
        //         $(".lds-spinner").show();
        //
        //         new Model('pos.order').call('search_read',[[['move_name', '=', credit_note_ncf],['returned_order', '=', true],['is_used_in_order', '=', false]]])
        //         .done(function(result){
        //
        //             if(result.length > 0){
        //
        //                 self.add_paymentline( cashregister );
        //                 var select_paymentline = self.selected_paymentline;
        //                 select_paymentline.set_returned_move_name(credit_note_ncf);
        //                 select_paymentline.set_returned_order_amount(-1*result[0].amount_total);
        //                 select_paymentline.set_amount(-1*result[0].amount_total);
        //                 self.pos.gui.screen_instances.payment.reset_input();
        //                 self.pos.gui.screen_instances.payment.render_paymentlines();
        //
        //                 $('.freeze_screen').removeClass("active_state");
        //                 $(".lds-spinner").hide();
        //
        //                 return true
        //
        //             }else{
        //                 $('.freeze_screen').removeClass("active_state");
        //                 $(".lds-spinner").hide();
        //
        //                 self.pos.gui.show_popup('error', {
        //                     'title': 'No existe',
        //                     'body': 'La nota de crédito '+ credit_note_ncf + ' no existe o ya fue utliziada'
        //                 });
        //
        //                 return false
        //             }
        //
        //
        //         })
        //         .fail(function(unused, event) {
        //             $('.freeze_screen').removeClass("active_state");
        //             $(".lds-spinner").hide();
        //
        //             self.pos.gui.show_popup('error', {
        //                 'title': 'Error en la conexión',
        //                 'body': 'Favor confirmar si la conexión con el servidor'
        //             });
        //
        //             return false
        //
        //         });
        //     }
        // }
    });

    // //this part is used for return orders:
    // models.load_models({
    //     model: 'pos.order',
    //     fields: [],
    //     domain: function(self) {
    //         var domain = [];
    //
    //         // state of orders
    //         var state = ['paid'];
    //         if (self.config.show_cancelled_orders) {
    //             state.push('cancel');
    //         }
    //         if (self.config.show_posted_orders) {
    //             state.push('done');
    //             state.push('invoiced');
    //         }
    //
    //         domain.push(['state','in',state]);
    //
    //         // number of orders
    //         if (self.config.load_orders_of_last_n_days) {
    //             var today = new Date();
    //             today.setHours(0,0,0,0);
    //             // load orders from the last date
    //             var last_date = new Date(today.setDate(today.getDate()-self.config.number_of_days)).toISOString();
    //             domain.push(['date_order','>=',last_date]);
    //         }
    //
    //         return domain;
    //     },
    //     condition: function(self) {
    //         return self.config.orders_history && !self.config.load_barcode_order_only;
    //     },
    //     loaded: function (self, orders) {
    //         self.update_orders_history(orders);
    //         self.order_ids = _.pluck(orders, 'id');
    //     },
    // });
    //
    // models.load_models({
    //     model: 'pos.order.line',
    //     fields: [],
    //     domain: function(self) {
    //         return [['order_id', 'in', self.order_ids]];
    //     },
    //     condition: function(self) {
    //         return self.config.orders_history && !self.config.load_barcode_order_only;
    //     },
    //     loaded: function (self, lines) {
    //         self.update_orders_history_lines(lines);
    //     },
    // });
    //
    // var _paylineproto = models.Paymentline.prototype;
    // models.Paymentline = models.Paymentline.extend({
    //     initialize: function (attributes, options) {
    //         _paylineproto.initialize.apply(this, arguments);
    //         this.returned_move_name = null;
    //         this.return_order_amount = 0 ;
    //
    //     },
    //
    //     set_returned_move_name: function (returned_move_name) {
    //         this.returned_move_name = returned_move_name;
    //     },
    //     get_returned_move_name: function() {
    //         return this.returned_move_name;
    //     },
    //     set_returned_order_amount: function (returned_order_amount) {
    //         this.returned_order_amount = returned_order_amount;
    //     },
    //     get_returned_order_amount: function() {
    //         return this.returned_order_amount;
    //     },
    //     export_as_JSON: function () {
    //         var loaded = _paylineproto.export_as_JSON.call(this);
    //         loaded.returned_move_name = this.get_returned_move_name();
    //         return loaded
    //     },
    //
    // });

    // var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_fiscal_type(id){
            var self = this;
            var res_fiscal_type = false;
            //TODO: try make at best performance
            self.fiscal_types.forEach(function (fiscal_type) {
			    if(fiscal_type.id === id){
			        res_fiscal_type = fiscal_type;
                }
            });
            if(res_fiscal_type){
                return res_fiscal_type
            }else{
                self.gui.show_popup('error', {
                    'title':_t('Fiscal type not found'),
                    'body': _t('This fiscal type not exist.'),
                });
                return false
            }
        }
    });

    return models
});
