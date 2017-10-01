odoo.define('ncf_pos.popups', function(require) {
    "use strict";

    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');

    var PaymentScreenTextInput = PopupWidget.extend({
        template: 'PaymentScreenTextInput',
        show: function(options) {
            window.document.body.removeEventListener('keypress', this.gui.current_screen.keyboard_handler);
            window.document.body.removeEventListener('keydown', this.gui.current_screen.keyboard_keydown_handler);
            options = options || {};
            this._super(options);

            this.renderElement();
            this.$('input,textarea').focus();

        },
        click_cancel: function() {
            window.document.body.addEventListener('keypress', this.gui.current_screen.keyboard_handler);
            window.document.body.addEventListener('keydown', this.gui.current_screen.keyboard_keydown_handler);
            this.gui.close_popup();
            if (this.options.cancel) {
                this.options.cancel.call(this);
            }
        },
        click_confirm: function() {
            window.document.body.addEventListener('keypress', this.gui.current_screen.keyboard_handler);
            window.document.body.addEventListener('keydown', this.gui.current_screen.keyboard_keydown_handler);
            var value = this.$('input,textarea').val();
            this.gui.close_popup();
            if (this.options.confirm) {
                this.options.confirm.call(this, value);
            }
        }
    });

    gui.define_popup({
        name: 'payment_screen_text_input',
        widget: PaymentScreenTextInput
    });
});
