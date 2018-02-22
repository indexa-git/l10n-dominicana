odoo.define('ncf_manager.ncf_manager', function (require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var FieldChar = field_registry.get('char');

    var FieldDgiiAutoComplete = FieldChar.extend({
        _prepareInput: function ($input) {
            var self = this;
            this.$input = $input || $("<input/>");
            this.$input.addClass('o_input');
            this.$input.attr({
                placeholder: this.attrs.placeholder || "",
            });
            this.$input.val(this._formatValue(this.value));

            this.$input.autocomplete({
                source: "/dgii_ws/",
                select: function (event, ui) {
                    var selected = ui.item.value.split("||");
                    self.$input.val(selected[1]);
                    var rnc = $('input[name$=\'vat\']');
                    rnc.val(selected[0]);
                    rnc.trigger('change');
                    return false;
                }
            });
            return this.$input;


        }
    });

    field_registry.add('dgii_autocomplete', FieldDgiiAutoComplete);

    return {
        FieldDgiiAutoComplete: FieldDgiiAutoComplete
    };

});