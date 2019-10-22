odoo.define('pos_ncf_manager.DB', function (require) {
    "use strict";

    var PosDB = require('point_of_sale.DB');
    var PosDBHistory = require('pos_orders_history.db');

    PosDB.include({

        _partner_search_string: function (partner) {
            var str = this._super(partner);
            str = str.replace('\n', '');
            if (partner.vat) {
                str += '|' + partner.vat;
            }
            return str + '\n';
        },

        get_sale_fiscal_sequence: function (sale_fiscal_type) {
            var sale_fiscal_type_sequence = this.sale_fiscal_sequences_by_id[sale_fiscal_type];
            if (!sale_fiscal_type_sequence) {
                this.gui.show_popup('error', {
                    'title': 'Error en el tipo de comprobante',
                    'body': 'Favor confirme el tipo de comprobante ya que' +
                        ' este tipo de comprobante no existe'
                });
                return;
            }
            return sale_fiscal_type_sequence
        },

        get_next_ncf_sequence: function (sale_fiscal_type) {

            function padLeft(nr, n, str) {
                return Array(n - String(nr).length + 1).join(str || '0') + nr;
            }

            var sale_fiscal_sequence = this.get_sale_fiscal_sequence(sale_fiscal_type);

            var sequence = sale_fiscal_sequence.prefix + padLeft(sale_fiscal_sequence.number_next_actual, sale_fiscal_sequence.padding);

            this.update_sale_fiscal_sequence(sale_fiscal_type, sale_fiscal_sequence.number_next_actual + 1);

            return sequence
        },

        update_sale_fiscal_sequence: function (sale_fiscal_type, nex_sequence) {

            var all_sale_fiscal_sequence = this.all_sale_fiscal_sequence;
            var sale_fiscal_sequences_by_id = this.sale_fiscal_sequences_by_id;

            sale_fiscal_sequences_by_id[sale_fiscal_type].number_next_actual = nex_sequence;

            for (var i = 0; i < all_sale_fiscal_sequence.length; i++) {
                if (all_sale_fiscal_sequence[i].sale_fiscal_type === sale_fiscal_type) {
                    all_sale_fiscal_sequence[i].number_next_actual = nex_sequence;
                }
            }

            this.save('all_sale_fiscal_sequence', all_sale_fiscal_sequence);
            this.save('sale_fiscal_sequences_by_id', sale_fiscal_sequences_by_id);
        },

    });

    PosDBHistory.include({

        _order_search_string: function (order) {
            var str = this._super(order);

            str = str.replace('\n', '');
            if (order.move_name) {
                str += '|' + order.move_name;
            }
            return str + '\n';
        },

    })

});
