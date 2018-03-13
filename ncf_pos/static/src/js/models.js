odoo.define('ncf_pos.models', function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var rpc = require('web.rpc');

    models.load_fields("res.partner", ['sale_fiscal_type']);


    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.sale_fiscal_type_selection = [];
            this.get_sale_fiscal_type_selection();
            return _super_posmodel.initialize.call(this, session, attributes);
        },
        set_sale_fiscal_type_selection: function (result) {
            if (result)
                this.sale_fiscal_type_selection = result;
        },
        get_sale_fiscal_type_selection: function () {
            var self = this;

            rpc.query({
                model: 'res.partner',
                method: 'get_sale_fiscal_type_selection',
                args: []
            }, {})
                .then(function (result) {
                    self.set_sale_fiscal_type_selection(result);
                });
        }
    }),

    models.Order = models.Order.extend({
        is_to_invoice: function(){
            return true ;     
        }
    })

});