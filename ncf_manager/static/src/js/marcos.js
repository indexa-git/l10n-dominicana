odoo.define('web.ncf_manager', function (require) {
    "use strict";

    var relational_fields = require('web.relational_fields');

    relational_fields.FieldMany2One.include({

        /**
         * If quickcreate is partner_id search on DGII_WS to auto create
         *
         * @private
         * @override method from field FieldMany2One
         * @param {view}, {id}, {context}
         */
        _searchCreatePopup: function (view, ids, context) {
            var _super = this._super.bind(this);

            if (this.name === "partner_id") {
                return this._rpc({
                    "model": "dgii.ws",
                    "method": "vat_check",
                    "args": [context.default_name]
                }).then(function (result) {
                    if (result !== 0) {
                        context.default_name = result["name"] === "" ? result["commercial_name"] : result["name"];
                        context.default_vat = result["rnc"];
                        context.default_is_company = true;
                    }
                }).done(function () {
                    return _super(view, ids, context);
                });
            } else {
                return _super(view, ids, context);
            }

        }

    });


});