odoo.define('ncf_manager.reconciliation', function (require) {
    "use strict";

    var account = require('account.reconciliation');
    var core = require('web.core');
    var QWeb = core.qweb;

    account.abstractReconciliation.include({

        decorateMoveLine: function (line) {
            line.partial_reconcile = false;
            line.propose_partial_reconcile = false;
            line.q_due_date = line.date;
            line.q_amount = (line.debit !== 0 ? line.q_debit : "") + (line.credit !== 0 ? line.q_credit : "");
            line.q_label = line.name;
            var template_name = (QWeb.has_template(this.template_prefix + "reconciliation_move_line_details") ? this.template_prefix : "") + "reconciliation_move_line_details";
            line.q_popover = QWeb.render(template_name, {line: line});
            if (line.ref && line.ref !== line.name)
                line.q_label = line.q_label + " : " + line.ref;
        }
    });


});

