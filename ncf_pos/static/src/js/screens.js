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
     THE INVOICES LIST
     ======================================
     The invoiceslist displays the list of invoices,
     and allows the cashier to reoder and rewrite the invoices.
     */
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
            }).focus();

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
            var contents = this.$('.order-list-contents');

            contents.empty();
            this.pos.db.order_by_id = {};
            orders.forEach(function (order) {
                var rowHtml = QWeb.render('InvoicesLine', {widget: self, order: order});

                self.pos.db.order_by_id[order.id] = order;
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

    InvoicesListScreenWidget.include({
        show: function () {
            var self = this;
            var contents = this.$('.order-details-contents');
            var parent = this.$('.order-list').parent();

            this._super();
            contents.empty();
            parent.scrollTop(0);
            this.$('.order-list-contents').on('click', '.order-line', function (e) {
                self.line_select(e, $(this), parseInt($(this).data('id')));
            });
        },
        close: function () {
            this._super();
            this.$('.order-list-contents').off('click', '.order-line');
        },
        render_list: function (orders) {
            this.display_order_details('hide');
            this._super(orders);
        },
        line_select: function (event, $line, id) {
            var self = this;
            var order = self.pos.db.order_by_id[id];

            this.$('.order-list .lowlight').removeClass('lowlight');

            if ($line.hasClass('highlight')) {
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.display_order_details('hide');
            }
            else {
                var y;

                this.$('.order-list .highlight').removeClass('highlight');
                $line.addClass('highlight');
                this.selected_tr_element = $line;
                y = event.pageY - $line.parent().offset().top;
                this.display_order_details('show', order, y);
            }
        },
        display_order_details: function (visibility, order, clickpos) {
            var self = this;
            var contents = this.$('.order-details-contents');
            var parent = this.$('.order-list').parent();
            var scroll = parent.scrollTop();
            var height = contents.height();
            var new_height = 0;
            var orderlines = order && order.lines;
            var statements = [];

            if (visibility === 'show') {
                contents.empty();
                contents.append($(QWeb.render('OrderDetails',
                    {
                        widget: this,
                        order: order,
                        orderlines: orderlines,
                        statements: statements
                    })));
                new_height = contents.height();
                if (!this.details_visible) {
                    if (clickpos < scroll + new_height + 20) {
                        parent.scrollTop(clickpos - 20);
                    }
                    else
                        parent.scrollTop(parent.scrollTop() + new_height);
                }
                else
                    parent.scrollTop(parent.scrollTop() - height + new_height);

                this.$("#close_order_details").on("click", function () {
                    self.display_order_details('hide');
                });
            }
            else if (visibility === 'hide') {
                if (this.selected_tr_element) {
                    this.selected_tr_element.removeClass('highlight');
                    this.selected_tr_element.addClass('lowlight');
                }
                contents.empty();
                if (height > scroll) {
                    contents.css({height: height + 'px'});
                    contents.animate({height: 0}, 400,
                        function () {
                            contents.css({height: ''});
                        });
                }
                else
                    parent.scrollTop(parent.scrollTop() - height);
            }

            this.details_visible = (visibility === 'show');
        }
    });

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
                } else if (order.get_total_without_tax() >= 50000 && !has_vat(client)) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Factura sin Cedula de Cliente',
                        'body': 'El cliente debe tener una cedula si el total de la factura es igual o mayor a RD$50,000 o mas',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                } else if (self.has_fiscal_type(client, ["fiscal", "gov", "special"])) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Para el tipo de comprobante',
                        'body': 'No puede crear una factura con crédito fiscal si el cliente no tiene RNC o Cédula. Puede pedir ayuda para que el cliente sea registrado correctamente si este desea comprobante fiscal',
                        'cancel': function () {
                            self.gui.show_screen('products');
                        }
                    });
                } else if(order.get_total_with_tax() <= 0) {
                    self.gui.show_popup('error', {
                        'title': 'Error: Cantidad de articulos a pagar',
                        'body': 'La orden esta vacia, no existen articulos a pagar. Por favor elija algun articulo',
                        'cancel': function() {
                            self.gui.show_screen('products');
                        }
                    });
                } else {
                    order.orderlines.find(function(line) {
                        if (line.get_price_with_tax() < 0) {
                            self.gui.show_popup('error', {
                                'title': 'Error: Precio de producto',
                                'body': 'Ningun producto puede tener precio menor o igual a RD$0',
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
        },
        has_vat: function(client) {
            return client.vat;
        },
        has_fiscal_type: function(client, fiscal_types) {
            return _.contains(fiscal_types, client.sale_fiscal_type) && !has_vat(client);
        }
    });
});