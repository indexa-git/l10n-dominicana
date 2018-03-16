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
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_order.initialize.apply(this, arguments);

            var pos_default_partner = this.pos.config.pos_default_partner_id;

            if (this.pos.config.iface_invoicing) {
                this.to_invoice = true;

                if (pos_default_partner) {
                    var client = this.pos.db.get_partner_by_id(pos_default_partner[0]);

                    if (client)
                        this.set_client(client);
                }
            }
        }
    });
});