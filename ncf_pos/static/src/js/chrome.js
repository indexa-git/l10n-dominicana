odoo.define('ncf_pos.chrome', function (require) {
    "use strict";
    var chrome = require("point_of_sale.chrome");

    /* ------- Synch. Notifications ------- */

    // Displays if there are orders that could
    // not be submitted, and how many.

    chrome.SynchNotificationWidget = chrome.SynchNotificationWidget.include({
        start: function(){
            var self = this;
            this.pos.bind('change:synch', function(pos,synch){
                self.set_status(synch.state, synch.pending);
            });
            this.$el.click(function(){
                self.pos.push_and_invoice_order(null,{'show_error':true});
            });
        },
    });

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