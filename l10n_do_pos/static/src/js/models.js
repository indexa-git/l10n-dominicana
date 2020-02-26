odoo.define('l10n_do_pos.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var _super_order = models.Order.prototype;

    models.load_fields('res.partner', ['l10n_do_dgii_tax_payer_type',]);
    models.load_fields('account.journal', [
        'l10n_latam_use_documents',
        'l10n_do_sequence_ids',
    ]);

    models.load_models({
        model: 'account.journal',
        fields: ['name', 'l10n_latam_use_documents', 'l10n_do_sequence_ids'],
        domain: function (self) {
            return [['id', '=', self.config.invoice_journal_id[0]]];
        },
        loaded: function (self, journals) {
            self.invoice_journal = false;
            if (journals[0]) {
                self.invoice_journal = journals[0];
            }
        },
    });

    models.load_models({
        model: 'ir.sequence',
        fields: [
            'l10n_latam_document_type_id',
        ],
        domain: function (self) {
            return [
                ['id', 'in', self.invoice_journal.l10n_do_sequence_ids],
            ];
        },
        loaded: function (self, latam_sequences) {
            self.l10n_latam_sequences = latam_sequences;
            console.log('Sequences loaded:', latam_sequences);
        },
    });

    models.load_models({
        model: 'l10n_latam.document.type',
        fields: [
            'name',
            'code',
            'l10n_do_ncf_type',
            'is_vat_required',
            'internal_type',
            'doc_code_prefix',
            'country_id',
        ],
        domain: function () {
            return [
                ['internal_type', 'in', ['invoice']],
                ['active', '=', true],
            ];
        },
        loaded: function (self, latam_document_types) {
            self.l10n_latam_document_types = latam_document_types;
            console.log('Document types loaded:', latam_document_types);
        },
    });

    models.Order = models.Order.extend({
        initialize: function () {
            _super_order.initialize.apply(this, arguments);
            var self = this;
            this.l10n_latam_document_number = '';
            this.l10n_latam_sequence_id = false;
            this.l10n_latam_document_type_id = false;
            this.l10n_latam_document_type =
                self.pos.get_latam_document_type_by_prefix();
            this.to_invoice_backend = false;
            this.set_to_invoice(true);
            // this.ncf_l10n_do_origin_ncf = '';
            // this.ncf_expiration_date = '';
            // var client = self.get_client();
            // if (this.get_mode() === 'return') {
            //
            //     this.fiscal_type = self.pos.get_fiscal_type_by_prefix('B04');
            //
            // } else if (client) {
            //     if (client.sale_fiscal_type_id) {
            //         this.fiscal_type =
            //             self.pos.get_fiscal_type_by_id(client.sale_fiscal_type_id[0]);
            //     } else {
            //         this.fiscal_type =
            //             self.pos.get_fiscal_type_by_prefix('B02');
            //     }
            // }
            this.save_to_db();
        },

        set_latam_document_type: function (l10n_latam_document_type) {
            this.l10n_latam_document_type = l10n_latam_document_type;
            this.save_to_db();
            this.latam_document_type_changed();
        },

        get_latam_document_type: function () {
            return this.l10n_latam_document_type;
        },

        latam_document_type_changed: function () {
            var current_order = this.pos.get_order();
            var latam_document_type_name =
                current_order.l10n_latam_document_type.name || false;
            this.pos.gui.screen_instances.payment
                .$('.js_latam_document_type_name').text(latam_document_type_name);
            this.pos.gui.screen_instances.products
                .$('.js_latam_document_type_name').text(latam_document_type_name);
        },

        export_as_JSON: function () {

            var self = this;
            var loaded = _super_order.export_as_JSON.call(this);
            var current_order = self.pos.get_order();

            if (current_order) {
                loaded.l10n_latam_document_number =
                    current_order.l10n_latam_document_number;
                loaded.l10n_latam_sequence_id = current_order.l10n_latam_sequence_id;
                loaded.l10n_latam_document_type_id =
                    current_order.l10n_latam_document_type_id;
                loaded.to_invoice_backend = current_order.to_invoice_backend;
                // loaded.ncf_l10n_do_origin_ncf = current_order.ncf_l10n_do_origin_ncf;
                // loaded.ncf_expiration_date = current_order.ncf_expiration_date;
            }

            return loaded;
        },
        set_to_invoice: function(to_invoice) {
            _super_order.set_to_invoice.call(this, to_invoice);
            this.to_invoice_backend = to_invoice;
        },
        // For returned order (credit note)
        // add_payment_credit_note: function (credit_note_ncf, cashregister) {
        //     var self = this;
        //     var payment_lines = self.get_paymentlines();
        //     var is_on_payment_line = false;
        //
        //     payment_lines.forEach(
        //         function (payment_line) {
        //             if (payment_line.get_returned_ncf()) {
        //                 if (payment_line.get_returned_ncf() ===
        //                     credit_note_ncf) {
        //                     is_on_payment_line = true;
        //                 }
        //             }
        //         });
        //
        //     if (is_on_payment_line) {
        //
        //         self.pos.gui.show_popup('error', {
        //             'title': _t('The credit note is in the order'),
        //             'body': _t('Credit note ' + credit_note_ncf +
        //                 ' is in the order, please try again'),
        //         });
        //
        //         return false;
        //
        //     }
        //     // TODO: esta parte podria buscar mejor por la factura y
        //     //  no por la orden
        //     var domain = [
        //         ['ncf', '=', credit_note_ncf],
        //         ['returned_order', '=', true],
        //         ['is_used_in_order', '=', false],
        //     ];
        //     self.pos.loading_screen_on();
        //     rpc.query({
        //         model: 'pos.order',
        //         method: 'search_read',
        //         args: [domain],
        //         limit: 1,
        //     }, {
        //         timeout: 3000,
        //         shadow: true,
        //     }).then(function (result) {
        //
        //         if (result.length > 0) {
        //             self.add_paymentline(cashregister);
        //             var select_paymentline = self.selected_paymentline;
        //             select_paymentline.set_returned_ncf(credit_note_ncf);
        //             select_paymentline.set_returned_order_amount(
        //                 -1 * result[0].amount_total
        //             );
        //             select_paymentline.set_amount(
        //                 -1 * result[0].amount_total
        //             );
        //             self.pos.gui.screen_instances
        //                 .payment.reset_input();
        //             self.pos.gui.screen_instances
        //                 .payment.render_paymentlines();
        //             self.pos.loading_screen_off();
        //
        //         } else {
        //             self.pos.loading_screen_off();
        //             self.pos.gui.show_popup('error', {
        //                 'title': _t('Not exist'),
        //                 'body': _t('Credit mote number ' + credit_note_ncf +
        //                     ' does exist'),
        //             });
        //         }
        //     }, function (err, ev) {
        //         self.pos.loading_screen_off();
        //         console.log(err);
        //         console.log(ev);
        //         ev.preventDefault();
        //         var error_body =
        //             _t('Your Internet connection is probably down.');
        //         if (err.data) {
        //             var except = err.data;
        //             error_body = except.arguments ||
        //                 except.message || error_body;
        //         }
        //         self.gui.show_popup('error', {
        //             'title': _t('Error: Could not Save Changes'),
        //             'body': error_body,
        //         });
        //     });
        // },
    });

    models.PosModel = models.PosModel.extend({
        get_latam_document_type_by_id: function (id) {
            var self = this;
            var res_latam_document_type = false;
            // TODO: try make at best performance
            self.l10n_latam_document_types.forEach(function (latam_document_type) {
                if (latam_document_type.id === id) {
                    res_latam_document_type = latam_document_type;
                }
            });
            if (!res_latam_document_type) {
                res_latam_document_type = this.get_latam_document_type_by_prefix();
            }
            return res_latam_document_type;
        },

        get_l10n_latam_sequence_by_document_type_id: function (document_type_id) {
            var result = false;
            var self = this;
            self.l10n_latam_sequences.forEach(function (latam_sequence) {
                if (latam_sequence.l10n_latam_document_type_id[0] === document_type_id) {
                    result = latam_sequence;
                }
            });
            return result
        },

        get_latam_document_type_by_prefix: function (prefix) {
            var self = this;
            var res_latam_document_type = false;
            // TODO: try make at best performance
            if (!prefix)
                prefix = 'B02';
            self.l10n_latam_document_types.forEach(function (latam_document_type) {
                if (latam_document_type.doc_code_prefix === prefix) {
                    res_latam_document_type = latam_document_type;
                }
            });
            if (res_latam_document_type) {
                return res_latam_document_type;
            }
            self.gui.show_popup('error', {
                'title': _t('Fiscal document type not found'),
                'body': _t('This fiscal document type not exist.'),
            });
            return false;
        },

        loading_screen_on: function () {
            $('.freeze_screen_spinner').addClass("active_state");
        },

        loading_screen_off: function () {
            $('.freeze_screen_spinner').removeClass("active_state");
        },

    });

    // var _paylineproto = models.Paymentline.prototype;
    //
    // models.Paymentline = models.Paymentline.extend({
    //     initialize: function () {
    //         _paylineproto.initialize.apply(this, arguments);
    //         this.returned_ncf = null;
    //         this.returned_order_amount = 0;
    //     },
    //
    //     set_returned_ncf: function (returned_move_name) {
    //         this.returned_ncf = returned_move_name;
    //     },
    //     get_returned_ncf: function () {
    //         return this.returned_ncf;
    //     },
    //     set_returned_order_amount: function (returned_order_amount) {
    //         this.returned_order_amount = returned_order_amount;
    //     },
    //     get_returned_order_amount: function () {
    //         return this.returned_order_amount;
    //     },
    //     export_as_JSON: function () {
    //         var loaded = _paylineproto.export_as_JSON.call(this);
    //         loaded.returned_ncf = this.get_returned_ncf();
    //         return loaded;
    //     },
    // });

    return models;
});
