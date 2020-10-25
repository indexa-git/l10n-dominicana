odoo.define('l10n_do_pos.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;
    screens.PaymentScreenWidget.include({

        keyboard_off: function () {
            // That one comes from BarcodeEvents
            $('body').keypress(this.keyboard_handler);
            // That one comes from the pos, but we prefer to cover
            // all the basis
            $('body').keydown(this.keyboard_keydown_handler);
        },
        keyboard_on: function () {
            $('body').off('keypress', this.keyboard_handler);
            $('body').off('keydown', this.keyboard_keydown_handler);
        },

        renderElement: function () {
            this._super();
            var self = this;
            this.$('.js_set_latam_document_type').click(function () {
                self.click_set_latam_document_type();
            });
        },

        open_vat_popup: function () {
            var self = this;
            var current_order = self.pos.get_order();

            self.keyboard_on();
            self.gui.show_popup('textinput', {
                'title': _t('You need to select a customer with RNC/Céd for' +
                    ' this fiscal type, place writes RNC/Céd'),
                'vat': '',
                confirm: function (vat) {
                    self.keyboard_off();
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
                        self.keyboard_off();
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
                    self.keyboard_off();
                    if (!current_order.get_client()) {
                        current_order.set_latam_document_type(
                            this.pos.get_latam_document_type_by_prefix()
                        );
                    }
                },
            });
        },

        click_set_latam_document_type: function () {
            var self = this;
            var latam_document_type_list =
                _.map(self.pos.l10n_latam_document_types,
                    function (latam_document_type) {
                        if (latam_document_type.internal_type === 'invoice') {
                            return {
                                label: latam_document_type.name,
                                item: latam_document_type,
                            };
                        }
                        return false;
                    });

            self.gui.show_popup('selection', {
                title: _t('Select document type'),
                list: latam_document_type_list,
                confirm: function (latam_document_type) {
                    var current_order = self.pos.get_order();
                    var client = self.pos.get_client();
                    current_order.set_latam_document_type(latam_document_type);
                    if (latam_document_type.is_vat_required && !client) {
                        self.open_vat_popup();
                    }
                    if (latam_document_type.is_vat_required && client) {
                        if (!client.vat) {
                            self.open_vat_popup();
                        }
                    }
                },
                is_selected: function (latam_document_type) {
                    var order = self.pos.get_order();
                    return latam_document_type ===
                        order.l10n_latam_document_type;
                },
            });
        },

        order_is_valid: function (force_validation) {

            var self = this;
            var current_order = this.pos.get_order();
            var client = current_order.get_client();
            var total = current_order.get_total_with_tax();
            if (current_order.to_invoice_backend) {
                current_order.to_invoice = false;
                current_order.save_to_db();
            }

            if (total === 0) {
                this.gui.show_popup('error', {
                    'title': _t('Sale in'),
                    'body': _t('You cannot make sales in 0, please add a ' +
                        'product with value'),
                });
                return false;
            }

            if (self.pos.invoice_journal.l10n_latam_use_documents &&
                current_order.to_invoice_backend) {

                if (current_order.l10n_latam_document_type.is_vat_required &&
                    !client) {

                    this.gui.show_popup('error', {
                        'title': _t('Required document (RNC/Céd.)'),
                        'body': _t('For invoice fiscal type ' +
                            current_order.fiscal_type.name +
                            ' its necessary customer, please select customer'),
                    });
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    return false;

                }

                if (current_order.l10n_latam_document_type.is_vat_required &&
                    !client.vat) {

                    this.gui.show_popup('error', {
                        'title': _t('Required document (RNC/Céd.)'),
                        'body': _t('For invoice fiscal type ' +
                            current_order.l10n_latam_document_type.name +
                            ' it is necessary for the customer have ' +
                            'RNC or Céd.'),
                    });
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    return false;
                }

                if (total >= 250000.00 && (!client || !client.vat)) {
                    this.gui.show_popup('error', {
                        'title': _t('Sale greater than RD$ 250,000.00'),
                        'body': _t('For this sale it is necessary for the ' +
                            'customer have ID'),
                    });
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    return false;
                }

            }


            if (this._super(force_validation)) {
                return true;
            }

            if (current_order.to_invoice_backend) {
                current_order.to_invoice = true;
                current_order.save_to_db();
            }

            return false;

        },

        finalize_validation: function () {
            var self = this;
            var current_order = this.pos.get_order();
            var _super = this._super.bind(this);
            if (current_order.to_invoice_backend &&
                self.pos.invoice_journal.l10n_latam_use_documents &&
                !current_order.l10n_latam_document_number) {
                var latam_sequence =
                    self.pos.get_l10n_latam_sequence_by_document_type_id(
                        current_order.l10n_latam_document_type.id
                    );
                self.pos.loading_screen_on();
                rpc.query({
                    model: 'ir.sequence',
                    method: 'next_by_id',
                    args: [latam_sequence.id],
                }).then(function (res) {
                    self.pos.loading_screen_off();
                    current_order.l10n_latam_document_number = res;
                    current_order.l10n_latam_sequence_id = latam_sequence.id;
                    current_order.l10n_latam_document_type_id =
                        current_order.l10n_latam_document_type.id;
                    current_order.save_to_db();
                    console.log(res);
                    _super();
                }, function (err, ev) {
                    self.pos.loading_screen_off();
                    current_order.to_invoice = true;
                    current_order.save_to_db();
                    console.log(err);
                    console.log(ev);
                    ev.preventDefault();
                    var error_body =
                        _t('Your Internet connection is probably down.');
                    if (err.data) {
                        var except = err.data;
                        error_body = except.arguments ||
                            except.message || error_body;
                    }
                    self.gui.show_popup('error', {
                        'title': _t('Error: Could not Save Changes'),
                        'body': error_body,
                    });
                });
            } else {
                this._super();
            }
        },
    });
});
