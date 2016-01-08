
odoo.define('ncf_pos.screens', function (require) {
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var Model = require('web.DataModel');

    var QWeb = core.qweb;


    screens.ReceiptScreenWidget.include({

        render_receipt: function () {
            var self = this;
            var order = this.pos.get_order();

            new Model('pos.order').call("get_ncf", [order.name]).then(function (result) {

                var ncf = result.ncf;
                var fiscal_type = ncf.slice(10,11);
                var invoice_type;
                switch (fiscal_type) {
                    case "01":
                        invoice_type = "FACTURA CON VALOR FISCAL";
                        break;
                    case "02":
                        invoice_type = "FACTURA PARA CONSUMIDOR FINAL";
                        break;
                    case "14":
                        invoice_type = "FACTURA GUBERNAMENTAL";
                        break;
                    case "15":
                        invoice_type = "FACTURA PARA REGIMENES ESPECIALES";
                        break;
                    default:
                        invoice_type = "NOTA DE CREDITO";
                };

                var client = order.attributes.client;
                console.log(order);
                self.$('.pos-receipt-container').html(QWeb.render('PosTicket', {
                    widget: self,
                    order: order,
                    ncf: ncf,
                    client: client,
                    invoice_type: invoice_type,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines()
                }));

                //if (!order.attributes.client){
                //    $(".pos-sale-ticket br").slice(0,4)[1].nextSibling.nodeValue = "Cliente: "+client[0].name;
                //    $(".pos-sale-ticket br").slice(0,4)[2].nextSibling.nodeValue = "Cliente: "+client[0].name;
                //    $(".pos-sale-ticket br").slice(0,4)[3].nextSibling.nodeValue = "Cliente: "+client[0].name;
                //}

            });
        },

    });


});
