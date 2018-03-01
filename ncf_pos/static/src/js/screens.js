odoo.define('ncf_pos.screens', function (require) {
    "use strict";


    var screens = require('point_of_sale.screens');
   // var gui = require('point_of_sale.gui');

    screens.ClientListScreenWidget.include({
        display_client_details: function (visibility,partner,clickpos) {
            var self = this;

            this._super(visibility,partner,clickpos);
            var name_input = this.$('.dgiiws');

             
                name_input.autocomplete({
                    source: "/dgii_ws/",
                    minLength: 3,
                       
                });

        
        }

    })



});