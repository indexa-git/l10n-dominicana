odoo.define('ncf_pos.models', function(require) {
    "use strict";
    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');

    var SuperOrder = models.Order;

    models.load_fields('pos.config', ['default_partner_id']);
    models.load_fields('res.partner', ['sale_fiscal_type']);

    models.load_models({
        model: 'res.partner',
        fields: ['partner_id', 'sale_fiscal_type'],
        loaded: function (self) {
            self.sale_fiscal_type = [{"code": "final", "name": "Final"},
                {"code": "fiscal", "name": "Fiscal"},
                {"code": "gov", "name": "Gubernamental"},
                {"code": "special", "name": "Especiales"}];
        },
    });

    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            SuperOrder.prototype.initialize.call(this, attributes, options);
            var self = this;
            if (!self.get_client()) {
                var default_partner_id = self.pos.db.get_partner_by_id(self.pos.config.default_partner_id[0]);
                self.set_client(default_partner_id);
            }
        },
    });

});
