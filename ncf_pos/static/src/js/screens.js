/**
 * Created by eneldoserrata on 3/12/15.
 */
odoo.define('ncf_pos', function (require) {
    var screens = require('point_of_sale.screens');

    screens.PaymentScreenWidget.include({
        validate_order: function (force_validation) {
            alert("ok");
        }
    })


});
