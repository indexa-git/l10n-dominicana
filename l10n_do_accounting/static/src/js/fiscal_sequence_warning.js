odoo.define('l10n_do_accounting.fiscal_sequence_warning', function (require) {
    "use strict";

    var core = require('web.core');
    var KanbanModel = require('web.KanbanModel');
    var KanbanRenderer = require('web.KanbanRenderer');
    var KanbanView = require('web.KanbanView');
    var view_registry = require('web.view_registry');
    var QWeb = core.qweb;
    var _lt = core._lt;

    var FiscalSequenceWarningRenderer = KanbanRenderer.extend({
        events: _.extend({}, KanbanRenderer.prototype.events, {
            'click .o_go_to_fiscal_sequences': '_goToFiscalSequences',
        }),

        // --------------------------------------------------------------------
        // Private
        // --------------------------------------------------------------------
        // TODO: implement similar for changes
        // /**
        //  * Notifies the controller that the target has changed.
        //  *
        //  * @private
        //  * @param {string} target_name the name of the changed target
        //  * @param {string} value the new value
        //  */
        // _notifyTargetChange: function (target_name, value) {
        //     this.trigger_up('dashboard_edit_target', {
        //         target_name: target_name,
        //         target_value: value,
        //     });
        // },

        /**
         * @override
         * @private
         * @returns {Deferred}
         */
        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var values = self.state.fiscalSequencesValues;
                var fiscal_sequence_dashboard = QWeb.render(
                    'l10n_do_accounting.FiscalSequenceWarning', {
                        widget: self,
                        values: values,
                    });
                self.$el.prepend(fiscal_sequence_dashboard);
            });
        },

        // --------------------------------------------------------------------
        // Handlers
        // --------------------------------------------------------------------

        // TODO:/**
        //  * @private
        //  * @param {Event}
        //  */
        _goToFiscalSequences: function (Event) {
            Event.preventDefault();
            this.do_action({
                name: 'Fiscal Sequences',
                res_model: 'account.fiscal.sequence',
                views: [[false, 'list'], [false, 'form']],
                type: 'ir.actions.act_window',
                view_type: "list",
                view_mode: "list",
            });
        },
    });

    var FiscalSequenceWarningModel = KanbanModel.extend({

        /**
         * @override
         */
        init: function () {
            this.fiscalSequencesValues = {};
            this._super.apply(this, arguments);
        },

        // --------------------------------------------------------------------
        // Public
        // --------------------------------------------------------------------

        /**
         * @override
         */
        get: function (localID) {
            var result = this._super.apply(this, arguments);
            if (_.isObject(result)) {
                result.fiscalSequencesValues =
                    this.fiscalSequencesValues[localID];
            }
            return result;
        },

        /**
         * @override
         * @returns {Deferred}
         */
        load: function () {
            return this._loadFiscalSequence(
                this._super.apply(this, arguments)
            );
        },

        /**
         * @override
         * @returns {Deferred}
         */
        reload: function () {
            return this._loadFiscalSequence(
                this._super.apply(this, arguments)
            );
        },

        // --------------------------------------------------------------------
        // Private
        // --------------------------------------------------------------------

        // TODO: TESTING PASS/**
        //  * @private
        //  * @param {Deferred} super_def a deferred that resolves with a
        //  * dataPoint id
        //  * @returns {Deferred -> string} resolves to the dataPoint id
        //  */
        _loadFiscalSequence: function (super_def) {
            var self = this;
            var dashboard_def = this._rpc({
                model: 'account.fiscal.sequence',
                method: 'search_read',
                args: [[['state', '=', 'active']]],
            });
            return $.when(super_def, dashboard_def)
                .then(function (id, fiscalSequenceValues) {
                    var lowFiscalSequence = [];
                    fiscalSequenceValues.forEach(function (item) {
                        if (item.warning_gap >= item.sequence_remaining) {
                            lowFiscalSequence.push(item);
                        }
                    });
                    self.fiscalSequencesValues[id] = lowFiscalSequence;
                    return id;
                });
        },
    });

    var FiscalSequenceWarningView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Model: FiscalSequenceWarningModel,
            Renderer: FiscalSequenceWarningRenderer,
        }),
        display_name: _lt('Dashboard'),
        icon: 'fa-dashboard',
        searchview_hidden: true,
    });

    view_registry.add('fiscal_sequence_warning', FiscalSequenceWarningView);

    return {
        Model: FiscalSequenceWarningModel,
        Renderer: FiscalSequenceWarningRenderer,
    };

});
