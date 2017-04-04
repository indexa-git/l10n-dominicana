odoo.define('ncf_pos.db', function (require) {
    "use strict";
   var PosDB = require('point_of_sale.DB');

    var DB = PosDB.include({
        add_partners: function (partners) {
            var updated_count = 0;
            var new_write_date = '';
            var partner;
            for (var i = 0, len = partners.length; i < len; i++) {
                partner = partners[i];

                if (this.partner_write_date &&
                    this.partner_by_id[partner.id] &&
                    new Date(this.partner_write_date).getTime() + 1000 >=
                    new Date(partner.write_date).getTime()) {
                    // FIXME: The write_date is stored with milisec precision in the database
                    // but the dates we get back are only precise to the second. This means when
                    // you read partners modified strictly after time X, you get back partners that were
                    // modified X - 1 sec ago.
                    continue;
                } else if (new_write_date < partner.write_date) {
                    new_write_date = partner.write_date;
                }
                if (!this.partner_by_id[partner.id]) {
                    this.partner_sorted.push(partner.id);
                }
                this.partner_by_id[partner.id] = partner;

                updated_count += 1;
            }

            this.partner_write_date = new_write_date || this.partner_write_date;

            if (updated_count) {
                // If there were updates, we need to completely
                // rebuild the search string and the barcode indexing

                this.partner_search_string = "";
                this.partner_by_barcode = {};

                for (var id in this.partner_by_id) {
                    partner = this.partner_by_id[id];
                    console.log(partner.vat);
                    if (partner.barcode) {
                        this.partner_by_barcode[partner.barcode] = partner;
                    }
                    partner.address = (partner.street || '') + ', ' +
                        (partner.vat || '') + ' ' +
                        (partner.city || '') + ', ' +
                        (partner.country_id[1] || '');
                    this.partner_search_string += this._partner_search_string(partner);
                }
            }
            return updated_count;
        }
    });

    return DB
});

