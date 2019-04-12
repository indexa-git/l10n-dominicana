odoo.define('ncf_manager.ncf_manager', function (require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var FieldChar = field_registry.get('char');

    var FieldDgiiAutoComplete = FieldChar.extend({
        _prepareInput: function ($input) {
            this._super.apply(this, arguments);

            $input.autocomplete({
                source: "/dgii_ws/",
                minLength: 3,
                select: function (event, ui) {
                    var $rnc = $("input[name$='vat']");
                    $input.val(ui.item.name);
                    $rnc.val(ui.item.rnc).trigger("change");

                    return false;
                },
            });
        },
    });

    field_registry.add('dgii_autocomplete', FieldDgiiAutoComplete);

    return {
        FieldDgiiAutoComplete: FieldDgiiAutoComplete,
    };

});
