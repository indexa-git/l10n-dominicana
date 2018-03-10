odoo.define('ncf_pos.screens', function (require) {
    "use strict";

    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;

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
        },

        show: function () {
            var self = this;
            var inputSearch = this.$('.invoices_search');
            this._super();

            this.renderElement();
            //var invoices = self.pos.db.pos_all_invoices;
            //this.render_list(invoices, undefined);

            this.$('.button').click(function () {
                //self.render_list(invoices, this.value);
                self.perform_search(self.$('.invoices_search').val());
            });

            this.$('.back').click(function () {
                self.gui.back();
            });

            //var search_timeout = null;

            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.connect(this.$('.invoices_search'));
            }

            //this.$('.searchbox input').on('keypress', function (event) {
            this.$('.invoices_search').on('keypress', function (event) {
                if (event.which === 13)
                    self.perform_search(this.value);
            });

            this.$('.searchbox .search-clear').click(function () {
                self.clear_search();
            });
        },
        perform_search: function (query) {
            var self = this;

            $.ajax(
                {
                    url: "/orders_ws",
                    dataType: 'json',
                    type: 'GET',
                    data: {query: query}
                }).done(function (result) {
                    self.render_list(result && result.orders || [])
                }
            );

            /*rpc.query({
             //model: 'res.partner'
             model: 'pos.order',
             fields: ['id', 'name', 'date_order', 'partner_id', 'lines', 'pos_reference', 'invoice_id']
             }).then(function (result) {
             alert(result);
             console.log("result: " + result);
             },
             function (type, err) {
             console.log("Error: " + err);
             });*/

            //rpc.query({
            //    route: "/invoices_ws",
            //    /*method: "GET",*/
            //    /*params: {value: query}*/
            //}, {})
            //    .then(function (result) {
            //        alert(result);
            //        console.log("invoices_ws: " + result);
            //    });
        },
        clear_search: function () {
            //var customers = this.pos.db.get_partners_sorted(1000);
            //this.render_list(customers);
            this.$('.invoices_search')[0].value = '';
            this.$('.invoices_search').focus();
        },
        render_list: function (orders) {
            var self = this;
            var contents = this.$('.client-list-contents');

            contents.empty();
            $.each(orders, function (i, e) {
                var rowHtml = QWeb.render('InvoicesLine', {widget: self, order: e});
                contents.append(rowHtml);
            });
        },
        close: function () {
            this._super();
            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.hide();
            }
        },
    });
    gui.define_screen({name: 'invoiceslist', widget: InvoicesListScreenWidget});

});