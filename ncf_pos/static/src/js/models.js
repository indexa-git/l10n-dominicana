odoo.define('ncf_pos.models', function (require) {

    var models = require('point_of_sale.models');

    models.load_models({
        model: 'res.company',
        fields: ['currency_id', 'email', 'website', 'company_registry', 'vat', 'name', 'phone', 'partner_id',
            'country_id', 'tax_calculation_rounding_method', 'street', 'street2', "city", 'state_id', 'zip', 'country_id'],
        ids: function (self) {
            return [self.company.id];
        },
        loaded: function (self, companies) {
            self.company = companies[0];
        }
    });

    var _super_order = models.Order.prototype;

    models.Order = models.Order.extend({
        initialize: function (attr, options) {
            _super_order.initialize.call(this, attr, options);
            this.quotation_type = this.quotation_type || "";
        },
        set_quotation_type: function (quotation_type) {
            this.quotation_type = quotation_type;
            this.trigger('change', this);
        },
        get_quotation_type: function () {
            return this.quotation_type;
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.call(this);
            json.quotation_type = this.quotation_type;
            return json;
        }
    });

});
