// © 2018 Francisco Peñaló <frankpenalo24@gmail.com>

// This file is part of NCF Manager.

// NCF Manager is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// NCF Manager is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

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