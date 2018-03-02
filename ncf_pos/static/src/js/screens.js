odoo.define('ncf_pos.screens', function (require) {
    "use strict";


    var screens = require('point_of_sale.screens');
    // var gui = require('point_of_sale.gui');

    screens.ClientListScreenWidget.include({
        display_client_details: function (visibility, partner, clickpos) {
            var self = this;

            this._super(visibility, partner, clickpos);
            var name_input = this.$('input[name$=\'name\']');
            var $rnc = $("input[name$='vat']");


            name_input.autocomplete({
                source: "/dgii_ws/",
                minLength: 3,
                select: function (event, ui) {
                    
                    name_input.val(ui.item.name);
                    $rnc.val(ui.item.rnc);

                    return false;
                }

            });


        }

    })



});