odoo.define('ncf_pos.db', function (require) {
    "use strict";
    var pos_db = require('point_of_sale.DB');

    pos_db.include({
        _partner_search_string: function (partner) {
            var str = this._super(partner);
            console.log("count");
            str = str.replace('\n', '');
            if (partner.vat) {
                str += '|' + partner.vat;
            }
             return str + '\n';
        }
    });
});
