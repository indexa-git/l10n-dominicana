// © 2018 Kevin Jiménez <kevinjimenezlorenzo@gmail.com>

// This file is part of NCF Manager.

// NCF Manager is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// NCF Manager is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

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