odoo.define('ncf_pos.chrome', function (require) {
    "use strict";
    var chrome = require("point_of_sale.chrome");
    /**
     * Debug windows widget that appear in debug mode
     *
     */
    chrome.DebugWidget = chrome.DebugWidget.include({
        /**
         * Adding 'view ticket' option to debug ticket layout with easy
         */
        start: function(){
            this._super.apply(this, arguments);

            var self = this;
            this.$('.button.view_ticket').click(function () {
                console.log("Tiiiiicket!!");
                self.pos.gui.show_screen('receipt');
            });
            this.$('.button.view_products').click(function () {
                self.pos.gui.show_screen('products');
            });
        }
    });

});
