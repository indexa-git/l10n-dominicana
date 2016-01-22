odoo.define('ncf_pos.models', function (require) {

    var models = require('point_of_sale.models');
    var session = require('web.session');


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
        model:  'res.users',
        fields: ['name','company_id',
        'allow_payments','allow_delete_order','allow_discount','allow_edit_price','allow_delete_order',
            'allow_refund','allow_delete_order_line','allow_cancel','allow_cash_refund','allow_credit'],
        ids:    function(self){ return [session.uid]; },
        loaded: function(self,users){ self.user = users[0]; }
    });

    models.load_models({
            model: 'res.users',
            fields: ['name', 'pos_security_pin', 'groups_id', 'barcode',
            'allow_payments','allow_delete_order','allow_discount','allow_edit_price','allow_delete_order',
            'allow_refund','allow_delete_order_line','allow_cancel','allow_cash_refund','allow_credit'],
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

    var OrderlineSuper = models.Orderline;
    models.Orderline = models.Orderline.extend({
        initialize: function () {
            OrderlineSuper.prototype.initialize.apply(this, arguments);
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
        }
    });

});
