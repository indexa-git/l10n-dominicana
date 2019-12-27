odoo.define('dgii_report.dgii_report_widget', function (require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var UrlChar = field_registry.get('url');

    var UrlDgiiReportsWidget = UrlChar.extend({
        init: function () {
            this._super.apply(this, arguments);
	    
	    this.value = "dgii_reports/" + this.value;
        },
    });

    field_registry.add('dgii_reports_url', UrlDgiiReportsWidget);

    return {
        UrlDgiiReportsWidget: UrlDgiiReportsWidget,
    };

});
