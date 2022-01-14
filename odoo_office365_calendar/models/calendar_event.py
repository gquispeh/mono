# See LICENSE file for full copyright and licensing details.

import json
import simplejson
import http.client as httplib
from datetime import datetime, timedelta
from odoo import models, fields, api
from . import office365lib as ofs



class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    o365_event_id = fields.Char(string='Office-365 Event Id')

    @api.model
    def sync_datas(self, **kw):
        pool = self.env
        res_partner_obj = pool['res.partner']

        res_users_obj = pool['res.users']
        calendar_event_obj = pool['calendar.event']
        oauth_obj = pool['auth.oauth.provider']
        conn = httplib.HTTPSConnection('graph.microsoft.com')
        users = res_users_obj.search([])
        for user in users:
            refresh_token = user.microsoft_refresh_token
            if refresh_token:
                provider = pool['ir.model.data'].get_object_reference(
                    'odoo_microsoft_account', 'provider_microsoft')[1]
                oauth_provider_rec = oauth_obj.browse(provider)
                latest_token = oauth_obj.sudo().oauth_token(
                    'refresh_token',
                    oauth_provider_rec,
                    code=None,
                    refresh_token=refresh_token).get('access_token')
                conn.request("GET", "/v1.0/me/events", "", {
                    'Authorization': latest_token,
                    'Accept': 'application/json'
                })
                response = conn.getresponse().read()
                events = simplejson.loads(response)
                for event_dict in events.get('value'):
                    event_subject = event_dict.get('subject', False)
                    event_organizer = event_dict.get('organizer') \
                        .get('emailAddress').get('address', False)
                    event_attendees = event_dict.get('attendees', [])
                    event_is_all_day = event_dict.get('isAllDay', False)
                    event_body = event_dict.get('bodyPreview', False)
                    event_id = event_dict.get('id', False)
                    cal_events = calendar_event_obj.search([
                        ('o365_event_id', '=', event_id)
                    ])
                    if not cal_events:
                        partner_ids = []
                        event_organizer_partner = res_partner_obj.search([
                            ('email', '=', event_organizer)
                        ], limit=1)
                        if event_organizer_partner:
                            partner_ids.append(event_organizer_partner.id)
                        else:
                            if event_dict.get(
                                    'organizer').get(
                                'emailAddress').get('name') and \
                                    event_dict.get('organizer').get(
                                        'emailAddress').get('address'):
                                partner_ids.append(
                                    res_partner_obj.create({
                                        'name': event_dict.get(
                                            'organizer').get(
                                            'emailAddress').get('name'),
                                        'email': event_dict.get(
                                            'organizer').get(
                                            'emailAddress').get('address'),
                                    }).id)
                        for attendee in event_attendees:
                            partners = res_partner_obj.search([
                                ('email', '=',
                                 attendee.get('emailAddress').get('address',
                                                                  False))
                            ], limit=1)
                            if partners:
                                partner_ids.append(partners.id)
                            else:
                                if attendee.get(
                                        'emailAddress').get('name') and \
                                        attendee.get(
                                            'emailAddress').get('address'):
                                    partner_ids.append(
                                        res_partner_obj.create({
                                            'name': attendee.get(
                                                'emailAddress').get('name'),
                                            'email': attendee.get(
                                                'emailAddress').get('address'),
                                        }).id)
                        create_vals = {
                            'name': event_subject,
                            'description': event_body,
                            'partner_ids': [(6, 0, list(set(partner_ids)))],
                            'user_id': user.id,
                            'o365_event_id': event_id,
                        }
                        if event_dict.get('isAllDay'):
                            start_date = datetime.strptime(
                                event_dict.get(
                                    'start', False).get('dateTime')[:-8] + 'Z',
                                "%Y-%m-%dT%H:%M:%SZ")
                            end_date = datetime.strptime(
                                event_dict.get(
                                    'end', False).get('dateTime')[:-8] + 'Z',
                                "%Y-%m-%dT%H:%M:%SZ")
                            end_date = end_date - timedelta(days=1)
                            create_vals.update({
                                'allday': event_is_all_day,
                                'start': str(start_date),
                                'stop': str(end_date),
                            })
                        else:
                            start_date = datetime.strptime(
                                event_dict.get('start', False).get(
                                    'dateTime')[:-8] + 'Z',
                                "%Y-%m-%dT%H:%M:%SZ")
                            end_date = datetime.strptime(
                                event_dict.get('end', False).get(
                                    'dateTime')[:-8] + 'Z',
                                "%Y-%m-%dT%H:%M:%SZ")
                            create_vals.update({
                                'start_datetime': str(start_date),
                                'stop_datetime': str(end_date),
                                'start': str(start_date),
                                'stop': str(end_date),
                            })
                        try:
                            event_id = calendar_event_obj. \
                                search([('name', '=', event_subject)], limit=1)
                            if not event_id:
                                calendar_event_obj.with_context(
                                    sync=True).create(create_vals)
                            self.env.cr.commit()
                        except BaseException:
                            pass
                for cal_rec in calendar_event_obj.search(
                        [('o365_event_id', '=', False)]):
                    attandees = []
                    for partner_rec in cal_rec.partner_ids:
                        attandees.append({"EmailAddress": {
                            "Address": str(partner_rec.email),
                            "Name": str(partner_rec.name),
                        }, "Type": "Required"})
                    conn = httplib.HTTPSConnection('graph.microsoft.com')
                    isAllday = 'false'
                    start_time = (str(cal_rec.start_datetime)).replace(
                        ' ', 'T')
                    stop_time = (str(cal_rec.stop_datetime)).replace(' ', 'T')
                    if cal_rec.allday:
                        isAllday = 'true'
                        start_time = str(
                            cal_rec.start_date) + 'T00:00:00.0000000'
                        stop_time = (str(datetime.strptime(
                            str(cal_rec.stop_date), "%Y-%m-%d") + timedelta(
                            days=1))).replace(' ', 'T')
                    data = """{
        "Subject": "%s",
        "Body": {
        "ContentType": "HTML",
        "Content": "%s"
        },
        "isAllDay": "%s",
        "Start": {
          "DateTime": "%s",
          "TimeZone": "UTC"
        },
        "End": {
          "DateTime": "%s",
          "TimeZone": "UTC"
        },
        "Attendees": %s
        }""" % (
                        cal_rec.name,
                        cal_rec.description or '',
                        isAllday, start_time,
                        stop_time, str(attandees)
                    )
                    conn.request("POST", "/v1.0/me/events", data, headers={
                        'Authorization': latest_token,
                        'Content-Type': 'application/json'})
                    response = conn.getresponse().read()
                    events = simplejson.loads(response)
                    cal_rec.with_context(sync=True).write({
                        'o365_event_id': events.get('id', '')
                    })
                    self.env.cr.commit()
        return True

    def fetch_token(self):
        provider = self.env['ir.model.data'].get_object_reference(
            'odoo_microsoft_account', 'provider_microsoft')[1]
        oauth_obj = self.env['auth.oauth.provider']
        res_users_obj = self.env['res.users']
        oauth_provider_rec = oauth_obj.browse(provider)
        refresh_token = res_users_obj.browse(
            self._uid).microsoft_refresh_token
        if not refresh_token:
            return False
        latest_token = oauth_obj.oauth_token(
            'refresh_token',
            oauth_provider_rec,
            code=None,
            refresh_token=refresh_token).get('access_token')
        return latest_token or ''

    def values_build(self, vals):
        start_time = (str(self.start_datetime)).replace(' ', 'T')
        stop_time = (str(self.stop_datetime)).replace(' ', 'T')
        isAllday = 'false'
        if self.allday:
            isAllday = 'true'
            start_time = str(self.start_date) + 'T00:00:00.0000000'
            stop_time = (str(
                datetime.strptime(str(self.stop_date), "%Y-%m-%d") +
                timedelta(days=1))).replace(' ', 'T')
        vals = {
            "Subject": self.name,
            "Body": {
                "ContentType": "HTML",
                "Content": self.description or ''
            },
            "isAllDay": isAllday,
            "Start": {
                "DateTime": start_time,
                "TimeZone": "UTC"
            },
            "End": {
                "DateTime": stop_time,
                "TimeZone": "UTC"
            },
            "Attendees": [{'Type': 'Required',
                           'EmailAddress': {'Name': self.user_id.name,
                                            'Address': self.user_id.email}}]
        }
        return vals

    def create_in_calendar(self, vals, res):
        office365 = ofs.Office365(self.fetch_token())
        value = res.values_build(vals)
        ofsresponse = office365.makerequest('POST', 'events', value)
        ofsresponse = json.loads(ofsresponse)
        if ofsresponse and ofsresponse.get('id'):
            res.o365_event_id = ofsresponse.get('id')

    def write_in_calendar(self, vals, rec):
        if rec.o365_event_id:
            office365 = ofs.Office365(rec.fetch_token())
            value = rec.values_build(vals)
            office365.makerequest(
                'PATCH', 'events/' + rec.o365_event_id, value)

    @api.model
    def create(self, vals):
        res = super(CalendarEvent, self).create(vals)
        self.with_delay().create_in_calendar(vals, res)
        return res

    def write(self, vals):
        res = super(CalendarEvent, self).write(vals)
        for rec in self:
            self.with_delay().write_in_calendar(vals, rec)
        return res

    def unlink(self):
        for rec in self:
            if rec.o365_event_id:
                office365 = ofs.Office365(rec.fetch_token())
                try:
                    office365.makerequest('DELETE', 'events/' +
                                          rec.o365_event_id, {})
                except BaseException:
                    pass
        return super(CalendarEvent, self).unlink()
