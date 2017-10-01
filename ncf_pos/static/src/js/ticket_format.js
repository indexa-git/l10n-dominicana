odoo.define('ncf_pos.ticket_format', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');

    function space_pad(num,size){
        var s = ""+num;
        while (s.length < size) {
            s = s + " ";
        }
        return s;
    }

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        generate_wrapped_orderline_product_name: function() {

            //For Order line product name wrapped
            var MAX_LENGTH = 17; // 40 * line ratio of .6
            var wrapped = [];
            var name = this.get_product().display_name;
            var current_line = "";

            while (name.length > 0) {
                var space_index = 16;//name.indexOf(" ");

                if (space_index === -1) {
                    space_index = name.length;
                }

                if (current_line.length + space_index > MAX_LENGTH) {
                    if (current_line.length) {
                        wrapped.push(current_line);
                    }
                    current_line = "";
                }

                current_line += name.slice(0, space_index + 1);
                name = name.slice(space_index + 1);
            }

            if (current_line.length) {
                wrapped.push(current_line);
            }

          //For product comment wrapped
            if(this.pos.config.on_product_line){
                if(this.get_order_line_comment() && this.get_order_line_comment().length > 0){
                    var order_line_comment = this.get_order_line_comment();
                    var current_order_line_comment = "";

                    while (order_line_comment.length > 0) {
                        var comment_space_index = 16;//name.indexOf(" ");

                        if (comment_space_index === -1) {
                            comment_space_index = order_line_comment.length;
                        }

                        if (current_order_line_comment.length + comment_space_index > MAX_LENGTH) {
                            if (current_order_line_comment.length) {
                                wrapped.push(current_order_line_comment);
                            }
                            current_order_line_comment = "";
                        }

                        current_order_line_comment += order_line_comment.slice(0, comment_space_index + 1);
                        order_line_comment = order_line_comment.slice(comment_space_index + 1);
                    }

                    if (current_order_line_comment.length) {
                        wrapped.push(current_order_line_comment);
                    }
                }
            }

           //For Discount wrapped
            if(this.get_discount() > 0){
                var discount_name = "With a " + this.get_discount().toString()+" % discount";
                var current_discount_line = "";

                while (discount_name.length > 0) {
                    var discount_space_index = 16;//name.indexOf(" ");

                    if (discount_space_index === -1) {
                        discount_space_index = discount_name.length;
                    }

                    if (current_discount_line.length + discount_space_index > MAX_LENGTH) {
                        if (current_discount_line.length) {
                            wrapped.push(current_discount_line);
                        }
                        current_discount_line = "";
                    }

                    current_discount_line += discount_name.slice(0, discount_space_index + 1);
                    discount_name = discount_name.slice(discount_space_index + 1);
                }

                if (current_discount_line.length) {
                    wrapped.push(current_discount_line);
                }
            }
            return wrapped;
        },
        generate_wrapped_quantity_str: function(string_name) {
            var MAX_LENGTH = 5; // 40 * line ratio of .6
            var wrapped = [];
            var name = this.get_quantity_str_with_unit();
            var current_line = "";

            while (name.length > 0) {
                var space_index = 4;//name.indexOf(" ");

                if (space_index === -1) {
                    space_index = name.length;
                }

                if (current_line.length + space_index > MAX_LENGTH) {
                    if (current_line.length) {
                        current_line = space_pad(current_line,5);
                        wrapped.push(current_line);
                    }
                    current_line = "";
                }

                current_line += name.slice(0, space_index + 1);
                name = name.slice(space_index + 1);
            }

            if (current_line.length) {
                current_line = space_pad(current_line,5);
                wrapped.push(current_line);
            }

            return wrapped;
        },
    });
});
