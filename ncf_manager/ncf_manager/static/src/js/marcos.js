odoo.define('ncf_manager.widgets', function (require) {
    "use strict";


    var form_common = require('web.form_common');
    var core = require('web.core');

    var Copyright = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
        start: function () {
            this.$el.append("<a href='https://marcos.do/page/opl?' target='_blank'>&#169; Marcos Organizador de Negocios SRL / Odoo Proprietary License v1.0</a>");
        }
    });

    core.form_custom_registry.add("opl", Copyright);

});