odoo.define('ncf_pos.models', function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var rpc = require('web.rpc');

    models.load_fields("res.partner", ['sale_fiscal_type']);
    models.load_fields("pos.config", ['pos_default_partner_id']);

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var self = this;
            this.invoices = [];
            this.sale_fiscal_type_selection = [];

            _super_posmodel.initialize.call(this, session, attributes);
        },

        load_server_data: function () {
            this.get_sale_fiscal_type_selection();

            return _super_posmodel.load_server_data.call(this);
        },

        get_sale_fiscal_type_selection: function () {
            var self = this;

            rpc.query({
                model: 'res.partner',
                method: 'get_sale_fiscal_type_selection',
                args: []
            }, {})
                .then(function (result) {
                    self.sale_fiscal_type_selection = result;
                });
        },
    })
});