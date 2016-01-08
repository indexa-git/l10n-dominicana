odoo.define('ncf_pos.models', function (require) {

    var models = require('point_of_sale.models');

    models.load_models({
        model: 'res.company',
        fields: ['currency_id', 'email', 'website', 'company_registry', 'vat', 'name', 'phone', 'partner_id',
            'country_id', 'tax_calculation_rounding_method', 'street','street2', "city", 'state_id', 'zip', 'country_id'],
        ids: function (self) {
            return [self.company.id];
        },
        loaded: function (self, companies) {
            self.company = companies[0];
        },
    });

});
