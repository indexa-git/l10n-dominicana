odoo.define('ncf_manager.ncf_manager', function (require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var FieldChar = field_registry.get('char');

    var basic_fields = require('web.basic_fields');
    var DebouncedField = basic_fields.DebouncedField;


    var FieldDgiiAutoComplete = FieldChar.extend({
        // template: "FieldDgiiAutoComplete",
        // events: {},
        // events: _.extend({}, DebouncedField.prototype.events, {
        // 'input': none,
        // 'change': none
        // }),
        // DEBOUNCE: false,
        _prepareInput: function ($input) {

            this.$input = $input || $("<input/>");
            this.$input.addClass('o_input');
            this.$input.attr({
                placeholder: this.attrs.placeholder || "",
            });
            this.$input.val(this._formatValue(this.value));

            this.$input.autocomplete({
                source: "/dgii_ws/"+this.$input.val()
            });

            return this.$input;

        }
    });

    field_registry.add('dgii_autocomplete', FieldDgiiAutoComplete);

    return {
        FieldDgiiAutoComplete: FieldDgiiAutoComplete
    };

});