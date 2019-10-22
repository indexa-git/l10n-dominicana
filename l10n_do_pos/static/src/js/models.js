odoo.define('l10n_do_pos.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var _super_order = models.Order.prototype;

    models.load_fields('res.partner', ['sale_fiscal_type_id']);
    models.load_fields('account.journal', ['is_for_credit_notes']);

    models.load_models({
        model: 'account.journal',
        fields: ['name', 'fiscal_journal'],
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
        model: 'account.fiscal.sequence',
        fields: ['name', 'fiscal_type_id'],
        domain: function (self) {
            return [
                ['state', '=', 'active'],
                ['type', '=', 'sale'],
                ['company_id', '=', self.company.id]
            ];
        },
        loaded: function (self, fiscal_sequences) {
            self.fiscal_sequences = fiscal_sequences
        },
    });

    models.load_models({
        model: 'account.fiscal.type',
        fields: [
            'name',
            'fiscal_position_id',
            'required_document',
            'prefix',
            'internal_generate'
        ],
        domain: function (self) {
            return [['type', 'in', ['sale', 'special_sale']]];
        },
        loaded: function (self, fiscal_types) {
            self.fiscal_types = fiscal_types
        },
    });

    models.Order = models.Order.extend({
        initialize: function () {
            _super_order.initialize.apply(this, arguments);

            var self = this;
            this.ncf = '';
            this.ncf_origin_out = '';
            this.ncf_expiration_date = '';
            this.fiscal_type = false;
            this.fiscal_type_id = false;
            this.fiscal_sequence_id = false;
            var client = self.get_client();

            if (this.get_mode() === 'return') {

                this.fiscal_type =
                    self.pos.get_fiscal_type_by_prefix(
                        'B04'
                    )

            } else {
                if (client) {
                    if (client.sale_fiscal_type_id) {
                        this.fiscal_type =
                            self.pos.get_fiscal_type_by_id(
                                client.sale_fiscal_type_id[0]
                            )
                    } else {
                        this.fiscal_type =
                            self.pos.get_fiscal_type_by_prefix(
                                'B02'
                            )
                    }
                } else {
                    this.fiscal_type =
                        self.pos.get_fiscal_type_by_prefix(
                            'B02'
                        )
                }
            }
            this.save_to_db();
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
            this.pos.gui.screen_instances.payment
                .$('.js_fiscal_type_name').text(fiscal_type_name);
            this.pos.gui.screen_instances.products
                .$('.js_fiscal_type_name').text(fiscal_type_name);
        },


        export_as_JSON: function () {

            var self = this;
            var loaded = _super_order.export_as_JSON.call(this);
            var current_order = self.pos.get_order();

            if (self.pos.get_order()) {
                loaded.ncf = current_order.ncf;
                loaded.ncf_origin_out = current_order.ncf_origin_out;
                loaded.ncf_expiration_date = current_order.ncf_expiration_date;
                loaded.fiscal_type_id = current_order.fiscal_type_id;
                loaded.fiscal_sequence_id = current_order.fiscal_sequence_id;
            }

            return loaded;

        },
    });

    models.PosModel = models.PosModel.extend({
        get_fiscal_type_by_id: function (id) {
            var self = this;
            var res_fiscal_type = false;
            //TODO: try make at best performance
            self.fiscal_types.forEach(function (fiscal_type) {
                if (fiscal_type.id === id) {
                    res_fiscal_type = fiscal_type;
                }
            });
            if (res_fiscal_type) {
                return res_fiscal_type
            } else {
                self.gui.show_popup('error', {
                    'title': _t('Fiscal type not found'),
                    'body': _t('This fiscal type not exist.'),
                });
                return false
            }
        },
        get_fiscal_type_by_prefix: function (prefix) {
            var self = this;
            var res_fiscal_type = false;
            console.log(self)
            //TODO: try make at best performance
            self.fiscal_types.forEach(function (fiscal_type) {
                if (fiscal_type.prefix === prefix) {
                    res_fiscal_type = fiscal_type;
                }
            });
            if (res_fiscal_type) {
                return res_fiscal_type
            } else {
                self.gui.show_popup('error', {
                    'title': _t('Fiscal type not found'),
                    'body': _t('This fiscal type not exist.'),
                });
                return false
            }
        }
    });

    return models
});
