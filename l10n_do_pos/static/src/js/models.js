odoo.define('l10n_do_pos.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var core = require('web.core');
    var _t = core._t;
    var _super_order = models.Order.prototype;

    models.load_fields('res.partner', ['l10n_do_dgii_tax_payer_type']);
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
                .$('.js_latam_document_type_name').text(
                    latam_document_type_name);
            this.pos.gui.screen_instances.products
                .$('.js_latam_document_type_name').text(
                    latam_document_type_name);
        },

        export_as_JSON: function () {

            var self = this;
            var loaded = _super_order.export_as_JSON.call(this);
            var current_order = self.pos.get_order();

            if (current_order) {
                loaded.l10n_latam_document_number =
                    current_order.l10n_latam_document_number;
                loaded.l10n_latam_sequence_id =
                    current_order.l10n_latam_sequence_id;
                loaded.l10n_latam_document_type_id =
                    current_order.l10n_latam_document_type_id;
                loaded.to_invoice_backend = current_order.to_invoice_backend;
            }

            return loaded;
        },
        set_to_invoice: function (to_invoice) {
            _super_order.set_to_invoice.call(this, to_invoice);
            this.to_invoice_backend = to_invoice;
        },
    });

    models.PosModel = models.PosModel.extend({
        get_latam_document_type_by_id: function (id) {
            var self = this;
            var res_latam_document_type = false;
            // TODO: try make at best performance
            self.l10n_latam_document_types.forEach(
                function (latam_document_type) {
                    if (latam_document_type.id === id) {
                        res_latam_document_type = latam_document_type;
                    }
            });
            if (!res_latam_document_type) {
                res_latam_document_type =
                    this.get_latam_document_type_by_prefix();
            }
            return res_latam_document_type;
        },

        get_l10n_latam_sequence_by_document_type_id: function (
            document_type_id) {
                var result = false;
                var self = this;
                self.l10n_latam_sequences.forEach( function (latam_sequence) {
                    if (latam_sequence.l10n_latam_document_type_id[0]
                        === document_type_id) {
                            result = latam_sequence;
                    }
                });
                return result
        },

        get_latam_document_type_by_prefix: function (prefix) {
            var self = this;
            var res_latam_document_type = false;
            // TODO: try make at best performance
            var real_prefix = prefix;
            if (!real_prefix) {
                real_prefix = 'B02';
            }
            self.l10n_latam_document_types.forEach(
                function (latam_document_type) {
                    if (latam_document_type.doc_code_prefix === real_prefix) {
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

    return models;
});
