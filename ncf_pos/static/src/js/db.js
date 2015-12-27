/**
 * Created by eneldoserrata on 12/12/15.
 */
odoo.define('ncf_pos', function (require) {
    "use strict";

    var db = require('point_of_sale.DB');

    db.include({
        _partner_search_string: function (partner) {
            var str = partner.name;
            if (partner.vat) {
                str += '|' + partner.vat;
            }
            if (partner.barcode) {
                str += '|' + partner.barcode;
            }
            if (partner.address) {
                str += '|' + partner.address;
            }
            if (partner.phone) {
                str += '|' + partner.phone.split(' ').join('');
            }
            if (partner.mobile) {
                str += '|' + partner.mobile.split(' ').join('');
            }
            if (partner.email) {
                str += '|' + partner.email;
            }
            str = '' + partner.id + ':' + str.replace(':', '') + '\n';
            return str;
        }
    });

});