odoo.define('ncf_manager.ncf_manager', function (require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var FieldChar = field_registry.get('char');


    var FieldDgiiAutoComplete = FieldChar.extend({
        // template: "FieldDgiiAutoComplete"
        attributes: {"autocomplete":"off"},
        className: "typeahead",
        start: function () {
            this._super.apply(this, arguments);
            var typeaheadSource = ['John', 'Alex', 'Terry'];

            this.$('input').typeahead({
                source: typeaheadSource
            });
            console.log(this.$('input'))

        }

    });

    field_registry.add('dgii_autocomplete', FieldDgiiAutoComplete);


});