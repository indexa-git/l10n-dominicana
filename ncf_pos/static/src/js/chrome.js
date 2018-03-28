odoo.define('ncf_pos.chrome', function (require) {
    "use strict";
    var chrome = require("point_of_sale.chrome");

    chrome.DebugWidget = chrome.DebugWidget.include({
        start: function(){
            var self = this;

            if (this.pos.debug) {
                this.show();
            }

            this.el.addEventListener('mouseleave', this.dragend_handler);
            this.el.addEventListener('mouseup',    this.dragend_handler);
            this.el.addEventListener('touchend',   this.dragend_handler);
            this.el.addEventListener('touchcancel',this.dragend_handler);
            this.el.addEventListener('mousedown',  this.dragstart_handler);
            this.el.addEventListener('touchstart', this.dragstart_handler);
            this.el.addEventListener('mousemove',  this.dragmove_handler);
            this.el.addEventListener('touchmove',  this.dragmove_handler);

            this.$('.toggle').click(function(){
                self.hide();
            });
            this.$('.button.set_weight').click(function(){
                var kg = Number(self.$('input.weight').val());
                if(!isNaN(kg)){
                    self.pos.proxy.debug_set_weight(kg);
                }
            });
            this.$('.button.reset_weight').click(function(){
                self.$('input.weight').val('');
                self.pos.proxy.debug_reset_weight();
            });
            this.$('.button.custom_ean').click(function(){
                var ean = self.pos.barcode_reader.barcode_parser.sanitize_ean(self.$('input.ean').val() || '0');
                self.$('input.ean').val(ean);
                self.pos.barcode_reader.scan(ean);
            });
            this.$('.button.barcode').click(function(){
                self.pos.barcode_reader.scan(self.$('input.ean').val());
            });
            this.$('.button.delete_orders').click(function(){
                self.gui.show_popup('confirm',{
                    'title': _t('Delete Paid Orders ?'),
                    'body':  _t('This operation will permanently destroy all paid orders from the local storage. You will lose all the data. This operation cannot be undone.'),
                    confirm: function(){
                        self.pos.db.remove_all_orders();
                        self.pos.set({synch: { state:'connected', pending: 0 }});
                    },
                });
            });
            this.$('.button.delete_unpaid_orders').click(function(){
                self.gui.show_popup('confirm',{
                    'title': _t('Delete Unpaid Orders ?'),
                    'body':  _t('This operation will destroy all unpaid orders in the browser. You will lose all the unsaved data and exit the point of sale. This operation cannot be undone.'),
                    confirm: function(){
                        self.pos.db.remove_all_unpaid_orders();
                        window.location = '/';
                    },
                });
            });

            this.$('.button.export_unpaid_orders').click(function(){
                self.gui.prepare_download_link(
                    self.pos.export_unpaid_orders(),
                    _t("unpaid orders") + ' ' + moment().format('YYYY-MM-DD-HH-mm-ss') + '.json',
                    ".export_unpaid_orders", ".download_unpaid_orders"
                );
            });

            this.$('.button.export_paid_orders').click(function() {
                self.gui.prepare_download_link(
                    self.pos.export_paid_orders(),
                    _t("paid orders") + ' ' + moment().format('YYYY-MM-DD-HH-mm-ss') + '.json',
                    ".export_paid_orders", ".download_paid_orders"
                );
            });

            this.$('.button.display_refresh').click(function () {
                self.pos.proxy.message('display_refresh', {});
            });

            this.$('.button.import_orders input').on('change', function(event) {
                var file = event.target.files[0];

                if (file) {
                    var reader = new FileReader();

                    reader.onload = function(event) {
                        var report = self.pos.import_orders(event.target.result);
                        self.gui.show_popup('orderimport',{report:report});
                    };

                    reader.readAsText(file);
                }
            });

            this.$('.button.view_ticket').click(function () {
                console.log("Tiiiiicket!!");
                self.pos.gui.show_screen('receipt');
            });

            this.$('.button.view_products').click(function () {
                self.pos.gui.show_screen('products');
            });

            _.each(this.events, function(name){
                self.pos.proxy.add_notification(name,function(){
                    self.$('.event.'+name).stop().clearQueue().css({'background-color':'#6CD11D'});
                    self.$('.event.'+name).animate({'background-color':'#1E1E1E'},2000);
                });
            });
        },
    });

});