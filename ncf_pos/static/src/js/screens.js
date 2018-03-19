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
            this._super();
            this.renderElement();

            this.$('.button').click(function () {
                self.perform_search(self.$('.invoices_search').val());
            });

            this.$('.back').click(function () {
                self.gui.back();
            });

            if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
                this.chrome.widget.keyboard.connect(this.$('.invoices_search'));
            }

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

            if ($.trim(query) == "") return false;

            rpc.query({
                model: 'pos.order',
                method: 'order_search_from_ui',
                args: [query]
            }, {})
                .then(function (result) {
                    self.render_list(result && result.orders || []);
                    console.log(result);
                });
        },
        clear_search: function () {
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

    screens.PaymentScreenWidget.include({
        show: function () {
            this._super();
            $(".button.js_invoice").remove();
        }
    });

    screens.ActionpadWidget.include({
        renderElement: function() {
            var self = this;
            this._super();

            this.$('.pay').on("click", function(){
                var order = self.pos.get_order();
                var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                    return line.has_valid_product_lot();
                });
                if(!has_valid_product_lot){
                    self.gui.show_popup('confirm',{
                        'title': _t('Empty Serial/Lot Number'),
                        'body':  _t('One or more product(s) required serial/lot number.'),
                        confirm: function(){
                            self.gui.show_screen('payment');
                        },
                    });
                }else{
                    self.gui.show_screen('payment');
                }

                // Here begin the method extension
                var client = self.pos.get_order().get_client();
                if (self.pos.config.iface_invoicing && !client) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Factura sin Cliente',
                        'body': 'Debe seleccionar un cliente para poder realizar el Pago, o utilizar el Cliente por defecto; de no tener un cliente por defecto, pida ayuda a su Encargado para que lo establezca.',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                } else if ((client.sale_fiscal_type == 'fiscal' || client.sale_fiscal_type == 'gov' || client.sale_fiscal_type == 'special') && (client.vat == false || client.vat == null)) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Para el tipo de comprobante',
                        'body': 'No puede crear una factura con crédito fiscal si el cliente no tiene RNC o Cédula. Puede pedir ayuda para que el cliente sea registrado correctamente si este desea comprobante fiscal',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                }

                if(order.get_total_with_tax() === 0) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Cantidad de articulos a pagar',
                        'body': 'La orden esta vacia, no existen articulos a pagar. Por favor elija algun articulo',
                        'cancel': function() {
                            self.gui.show_screen('products');
                        }
                    });
                } else {
                    order.orderlines.find(function(line) {
                        if (line.get_price_with_tax() <= 0) {
                            self.gui.show_popup('error', {
                                'title': 'Error: Precio de producto',
                                'body': 'Ningun producto puede tener precio 0 o menor',
                                'cancel': function() {
                                    self.gui.show_screen('products');
                                }
                            });

                            return true;
                        }
                    });
                }
                // Here end the method extension
            });

            this.$('.set-customer').click(function(){
                self.gui.show_screen('clientlist');
            });
        }
    });


});