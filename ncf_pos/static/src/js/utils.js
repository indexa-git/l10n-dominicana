$(function () {
    "use strict";

    jQuery.fn.extend({
        /**
         * Return the handler or an object array of the jQuery object events
         *
         * @param eventName {string} - Event name
         * @param [index=-1] {int} - Index of the object array to return
         * @returns {(array|object)} the handler or object array of the events
         * created to a jQuery object
         */
        getEvent: function (eventName, index=-1) {
            var events;

            if (!this.length) {
                return null;
            }
            events = $._data(this[0], "events");
            if (!events) {
                return null;
            } else if (!eventName) {
                return events;
            } else if ((events || {}).hasOwnProperty(eventName)) {
                if (index > -1 && index < events[eventName].length) {
                    return events[eventName][index].handler;
                } else {
                    return events[eventName];
                }
            }
        }
    });
});