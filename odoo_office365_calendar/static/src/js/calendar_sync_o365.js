odoo.define('o365_calendar.odoo_office365_calendar', function (require) {
"use strict";

	var core = require('web.core');
	var QWeb = core.qweb;
	var ajax = require('web.ajax');
    var CalendarController = require('web.CalendarController');
    var CalendarRenderer = require('web.CalendarRenderer');

CalendarRenderer.include({
    events: _.extend({}, CalendarRenderer.prototype.events, {
        'click #o365_calendar_sync': 'sync_o365_calendar',
    }),
    sync_o365_calendar: function(ev) {
        var self = this;
        $(ev.currentTarget).attr('disabled','disabled');
        ajax.jsonRpc('/o365_calendar/sync_data', {}).then(function(data){
            if (!data){
                alert('Access Token Not found.');
            }
            $(ev.currentTarget).removeAttr('disabled');
        })
    }
});

});
