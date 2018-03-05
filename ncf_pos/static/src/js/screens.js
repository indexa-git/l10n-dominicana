odoo.define('ncf_pos.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');

    screens.ClientListScreenWidget.include({
        display_client_details: function (visibility, partner, clickpos) {
            var self = this;

            this._super(visibility, partner, clickpos);
            var name_input = this.$('input[name$=\'name\']');
            var $rnc = $("input[name$='vat']");
            var $sale_fiscal_type = $("select[name$='sale_fiscal_type']");

            name_input.autocomplete({
                source: "/dgii_ws/",
                minLength: 3,
                select: function (event, ui) {
                    name_input.val(ui.item.name);
                    $rnc.val(ui.item.rnc);
                    $sale_fiscal_type.val("fiscal");

                    return false;
                }
            });
        }
    });

    /*--------------------------------------*\
     |         THE INVOICES LIST              |
     \*======================================*/

// The invoiceslist displays the list of invoices,
// and allows the cashier to reoder and rewrite the invoices.

    var InvoicesListScreenWidget = screens.ScreenWidget.extend({
        template: 'InvoicesListScreenWidget',

        init: function (parent, options) {
            this._super(parent, options);
            //this.partner_cache = new DomCache();
        },

        auto_back: true,

        show: function () {
            var self = this;
            this._super();
            //var invoices = self.pos.db.pos_all_invoices;
            //this.render_list(invoices, undefined);
            this.$('invoices_search').keyup(function () {
                //self.render_list(invoices, this.value);
            });

            this.$('.back').on('click', function () {
                self.gui.back();
            });

             this.$('.search').on('click', function () {
                alert("Llenar Grid");
            });
        },

        close: function() {
            this._super();
        },
    });
    gui.define_screen({name: 'invoiceslist', widget: InvoicesListScreenWidget});

});