odoo.define('ncf_pos.models', function (require) {
    'use strict';

    var models = require('point_of_sale.models');
    var session = require('web.session');

    //TODO load info for tracking serial number
    //models.load_models({
    //    model: 'product.template',
    //    fields: ['tracking'],
    //    domain: [['tracking', '!=', 'none']],
    //    loaded: function (self, products_tracking) {
    //        models.load_models({
    //            models: 'product.',
    //            fields: ['id'],
    //            domain: [['product_tmpl_id', 'in', '']]
    //
    //        });
    //    }
    //});


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
        },
        {
            model: 'res.users',
            fields: ['name', 'company_id'],
            ids: function (self) {
                return [session.uid];
            },
            loaded: function (self, users) {
                self.user = users[0];
            }
        });

    models.load_models({
        model: 'res.users',
        fields: ['name', 'company_id',
            'allow_payments', 'allow_delete_order', 'allow_discount', 'allow_edit_price', 'allow_delete_order',
            'allow_refund', 'allow_delete_order_line', 'allow_cancel', 'allow_cash_refund', 'allow_credit'],
        ids: function (self) {
            return [session.uid];
        },
        loaded: function (self, users) {
            self.user = users[0];
        }
    });

    models.load_models({
        model: 'res.users',
        fields: ['name', 'pos_security_pin', 'groups_id', 'barcode',
            'allow_payments', 'allow_delete_order', 'allow_discount', 'allow_edit_price', 'allow_delete_order',
            'allow_refund', 'allow_delete_order_line', 'allow_cancel', 'allow_cash_refund', 'allow_credit'],
        domain: function (self) {
            return [['company_id', '=', self.user.company_id[0]], '|', ['groups_id', '=', self.config.group_pos_manager_id[0]], ['groups_id', '=', self.config.group_pos_user_id[0]]];
        },
        loaded: function (self, users) {
            // we attribute a role to the user, 'cashier' or 'manager', depending
            // on the group the user belongs.
            var pos_users = [];
            for (var i = 0; i < users.length; i++) {
                var user = users[i];
                for (var j = 0; j < user.groups_id.length; j++) {
                    var group_id = user.groups_id[j];
                    if (group_id === self.config.group_pos_manager_id[0]) {
                        user.role = 'manager';
                        break;
                    } else if (group_id === self.config.group_pos_user_id[0]) {
                        user.role = 'cashier';
                    }
                }
                if (user.role) {
                    pos_users.push(user);
                }
                // replace the current user with its updated version
                if (user.id === self.user.id) {
                    self.user = user;
                }
            }
            self.users = pos_users;
        }
    });

    var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            PosModelSuper.prototype.initialize.apply(this, arguments);
        },
        set_cashier: function (user) {
            this.cashier = user;
            this.chrome.check_allow_delete_order();
        }
    });

    var _order_line_super = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function () {
            _order_line_super.initialize.apply(this, arguments);
            this.qty_allow_refund = this.qty_allow_refund || 0;
            this.refund_line_ref = this.refund_line_ref || false;
        },
        set_discount: function (discount) {
            var self = this;
            var cashier = self.pos.get_cashier();
            var disc = Math.min(Math.max(parseFloat(discount) || 0, 0), 100);
            if (disc <= cashier.allow_discount) {
                this.discount = disc;
                this.discountStr = '' + disc;
                this.trigger('change', this);
            }
        },
        set_qty_allow_refund: function (qty_allow_refund) {
            this.qty_allow_refund = qty_allow_refund;
            this.trigger('change', this);
        },
        get_qty_allow_refund: function () {
            return this.qty_allow_refund || 0;
        },
        set_refund_line_ref: function (refund_line_ref) {
            this.refund_line_ref = refund_line_ref || false;
            this.trigger('change', this)
        },
        get_refund_line_ref: function () {
            return this.refund_line_ref || false;
        },
        export_as_JSON: function () {
            var json = _order_line_super.export_as_JSON.apply(this, arguments);
            json.qty_allow_refund = this.get_qty_allow_refund();
            json.refund_line_ref = this.get_refund_line_ref();
            return json
        },
        export_for_printing: function () {
            var json = _order_line_super.export_for_printing.apply(this, arguments);
            json.qty_allow_refund = this.get_qty_allow_refund();
            json.refund_line_ref = this.get_refund_line_ref();
            return json;
        }
    });

    var PaymentlineSuper = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function () {
            PaymentlineSuper.initialize.apply(this, arguments);
            this.type = this.type || 'payment'
            return this;
        },
        set_type: function (type) {
            this.type = type;
            this.trigger("change", this);
        },
        get_type: function () {
            return this.type;
        },
        export_as_JSON: function () {
            var res = PaymentlineSuper.export_as_JSON.apply(this, arguments);
            res.type = this.get_type();
            return res;
        },
        export_for_printing: function () {
            var res = PaymentlineSuper.export_for_printing.apply(this, arguments);
            res.type = this.get_type();
            return res
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            _super_order.initialize.apply(this, arguments);
            var self = this;
            this.quotation_type = this.quotation_type || false;
            this.order_type = this.order_type || "order";
            this.origin = this.origin || false;
            this.origin_ncf = this.origin_ncf || false;
            this.credit = this.credit || 0;
            this.credit_ncf = this.credit_ncf || "";
            this.ncf = this.ncf || "";
            this.fiscal_type = this.fiscal_type || "";

            if (!self.get_client()) {
                var default_partner_id = self.pos.db.get_partner_by_id(self.pos.config.default_partner_id[0]);
                self.set_client(default_partner_id);
            }

            this.save_to_db();
        },
        init_from_JSON: function (json) {
            _super_order.init_from_JSON.apply(this, arguments);
            this.quotation_type = json.quotation_type;
            this.order_type = json.order_type;
            this.origin = json.origin;
            this.origin_ncf = json.origin_ncf;
        },
        get_order_note: function () {
            return $("#wk_note_id").val();
        },
        set_quotation_type: function (quotation_type) {
            this.quotation_type = quotation_type;
            this.trigger('change', this);
        },
        get_quotation_type: function () {
            return this.quotation_type || false;
        },
        set_order_type: function (order_type) {
            this.order_type = order_type;
            this.trigger('change', this);
        },
        get_order_type: function () {
            return this.order_type || "order";
        },
        set_origin: function (origin) {
            this.origin = origin;
            this.trigger('change', this);
        },
        get_origin: function () {
            return this.origin || false
        },
        set_ncf: function (ncf) {
            this.ncf = ncf;
            this.trigger('change', this);
        },
        get_ncf: function () {
            return this.ncf || false
        },
        set_origin_ncf: function (origin_ncf) {
            this.origin_ncf = origin_ncf;
            this.trigger('change', this);
        },
        get_origin_ncf: function () {
            return this.origin_ncf || false
        },
        set_credit: function (credit) {
            this.credit = credit;
            this.trigger('change', this)
        },
        get_credit: function () {
            return this.credit || 0;
        },
        set_credit_ncf: function (credit) {
            this.credit_ncf = credit;
            this.trigger('change', this)
        },
        get_credit_ncf: function () {
            return this.credit_ncf || 0;
        },
        set_fiscal_type: function (credit) {
            this.fiscal_type = credit;
            this.trigger('change', this)
        },
        get_fiscal_type: function () {
            return this.fiscal_type || 0;
        },
        add_product: function (product, options) {
            if (product.qty_allow_refund == 0 && this.get_order_type() == "refund") {
                return
            }

            if (this._printed) {
                this.destroy();
                return this.pos.get_order().add_product(product, options);
            }
            this.assert_editable();
            options = options || {};
            var attr = JSON.parse(JSON.stringify(product));
            attr.pos = this.pos;
            attr.order = this;


            var line = new models.Orderline({}, {pos: this.pos, order: this, product: product});

            if (this.get_order_type() == "refund") {
                line.set_unit_price(product.refund_price);
                line.set_discount(product.refund_discount);
                line.set_note(product.refund_note);
                line.set_qty_allow_refund(product.qty_allow_refund);
                line.set_refund_line_ref(product.refund_line_ref);
                product.qty_allow_refund--;
            }

            if (options.quantity !== undefined) {
                line.set_quantity(options.quantity);
            }
            if (options.price !== undefined) {
                line.set_unit_price(options.price);
            }
            if (options.discount !== undefined) {
                line.set_discount(options.discount);
            }

            if (options.extras !== undefined) {
                for (var prop in options.extras) {
                    line[prop] = options.extras[prop];
                }
            }

            var last_orderline = this.get_last_orderline();
            if (last_orderline && last_orderline.can_be_merged_with(line) && options.merge !== false) {
                last_orderline.merge(line);
            } else {
                this.orderlines.add(line);
            }
            this.select_orderline(this.get_last_orderline());
        },
        export_as_JSON: function () {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.quotation_type = this.get_quotation_type();
            json.order_type = this.get_order_type();
            json.origin = this.get_origin();
            json.origin_ncf = this.get_origin_ncf();
            json.credit = this.get_credit();
            json.credit_ncf = this.get_credit_ncf();
            json.ncf = this.get_ncf();
            json.fiscal_type = this.get_fiscal_type();
            json.order_note = this.get_order_note()
            return json;
        },
        export_for_printing: function () {
            var json = _super_order.export_for_printing.apply(this, arguments);
            json.quotation_type = this.get_quotation_type();
            json.order_type = this.get_order_type();
            json.origin = this.get_origin();
            json.origin_ncf = this.get_origin_ncf();
            json.credit = this.get_credit();
            json.credit_ncf = this.get_credit_ncf();
            json.ncf = this.get_ncf();
            json.fiscal_type = this.get_fiscal_type();
            return json
        }
    });


});
