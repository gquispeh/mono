# See LICENSE file for full copyright and licensing details.

import simplejson
import http.client as httplib
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request


class O365CalendarController(http.Controller):

    @http.route('/o365_calendar/sync_data', type='json', auth='user')
    def sync_data(self, **kw):
        pool = request.env
        res_partner_obj = pool['res.partner']
        res_users_obj = pool['res.users']
        calendar_event_obj = pool['calendar.event']
        oauth_obj = pool['auth.oauth.provider']
        conn = httplib.HTTPSConnection('graph.microsoft.com')
        provider = pool['ir.model.data'].sudo().get_object_reference(
            'odoo_microsoft_account',
            'provider_microsoft')[1]
        oauth_provider_rec = oauth_obj.sudo().browse(provider)
        refresh_token = res_users_obj.sudo().browse(request.uid) \
            .microsoft_refresh_token
        if not refresh_token:
            return False
        latest_token = oauth_obj.oauth_token(
            'refresh_token',
            oauth_provider_rec,
            code=None, refresh_token=refresh_token).get('access_token')
        conn.request("GET", "/v1.0/me/events", "", {
            'Authorization': latest_token,
            'Accept': 'application/json'
        })
        response = conn.getresponse().read()
        events = simplejson.loads(response)
        response_ids = []
        o365_event_ids = []
        if events and events.get('value'):
            for event in events.get('value'):
                response_ids.append(str(event.get('id')))
            for rec in calendar_event_obj.sudo().search(
                    [('user_id', '=', request.env.user.id)]):
                o365_event_ids.append(str(rec.o365_event_id))
            response_ids_1 = set(response_ids)
            o365_event_ids_1 = set(o365_event_ids)
            diff = o365_event_ids_1.difference(response_ids_1)
            diff = list(diff)
            rec_search = calendar_event_obj.sudo().search(
                [('o365_event_id', 'in', diff)])
            rec_search and rec_search.unlink()
            for event_dict in events.get('value'):
                event_subject = event_dict.get('subject', 'No Events Name') \
                                or 'No Events Name'
                event_organizer = event_dict.get('organizer') \
                    .get('emailAddress').get('address', False)
                event_attendees = event_dict.get('attendees', [])
                event_is_all_day = event_dict.get('isAllDay', False)
                event_body = event_dict.get('bodyPreview', False)
                event_id = event_dict.get('id', False)
                cal_events = calendar_event_obj.sudo().search([
                    ('o365_event_id', '=', event_id)
                ], limit=1)
                if not cal_events:
                    partner_ids = []
                    event_organizer_partner = res_partner_obj.sudo().search([
                        ('email', '=', event_organizer)
                    ], limit=1)
                    if event_organizer_partner:
                        partner_ids.append(event_organizer_partner.id)
                    else:
                        if event_dict.get('organizer').get(
                                'emailAddress').get('name') and \
                                event_dict.get('organizer').get(
                                    'emailAddress').get('address'):
                            partner_ids.append(
                                res_partner_obj.sudo().create({
                                    'name': event_dict.get(
                                        'organizer').get('emailAddress').get(
                                        'name'),
                                    'email': event_dict.get(
                                        'organizer').get(
                                        'emailAddress').get('address')
                                }).id)
                    for attendee in event_attendees:
                        partners = res_partner_obj.sudo().search([
                            ('email', '=', attendee.get('emailAddress').get(
                                'address', False))], limit=1)
                        if partners:
                            partner_ids.append(partners.id)
                        else:
                            if attendee.get(
                                    'emailAddress').get('name') and \
                                    attendee.get(
                                        'emailAddress').get('address'):
                                partner_ids.append(
                                    res_partner_obj.sudo().create({
                                        'name': attendee.get(
                                            'emailAddress').get('name'),
                                        'email': attendee.get(
                                            'emailAddress').get('address'),
                                    }).id)
                    create_vals = {
                        'name': event_subject,
                        'description': event_body,
                        'partner_ids': [(6, 0, list(set(partner_ids)))],
                        'user_id': request.env.user.id,
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
                                'dateTime')[:-8] + 'Z', "%Y-%m-%dT%H:%M:%SZ")
                        end_date = datetime.strptime(
                            event_dict.get('end', False).get(
                                'dateTime')[:-8] + 'Z', "%Y-%m-%dT%H:%M:%SZ")
                        create_vals.update({
                            'start_datetime': str(start_date),
                            'stop_datetime': str(end_date),
                            'start': str(start_date),
                            'stop': str(end_date),
                        })
                    calendar_event_obj.sudo().with_context(sync=True).create(
                        create_vals)
                else:
                    update_vals = {}
                    if cal_events.name != event_subject:
                        update_vals.update({
                            'name': event_subject
                        })
                    if cal_events.description != event_body:
                        update_vals.update({
                            'description': event_body
                        })
                    if cal_events.user_id.id != request.uid:
                        update_vals.update({
                            'user_id': request.env.user.id
                        })
                    if cal_events.o365_event_id != event_id:
                        update_vals.update({
                            'o365_event_id': event_id,
                        })

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
                        if cal_events.allday != event_is_all_day:
                            update_vals.update({
                                'allday': event_is_all_day,
                            })
                        if cal_events.start != str(start_date):
                            update_vals.update({
                                'start': str(start_date),
                            })
                        if cal_events.stop != str(end_date):
                            update_vals.update({
                                'stop': str(end_date),
                            })
                    else:
                        start_date = datetime.strptime(
                            event_dict.get('start', False).get(
                                'dateTime')[:-8] + 'Z', "%Y-%m-%dT%H:%M:%SZ")
                        end_date = datetime.strptime(
                            event_dict.get(
                                'end', False).get('dateTime')[:-8] + 'Z',
                            "%Y-%m-%dT%H:%M:%SZ")
                        if cal_events.allday != event_is_all_day:
                            update_vals.update({
                                'allday': event_is_all_day,
                            })
                        if cal_events.start_datetime != str(start_date):
                            update_vals.update({
                                'start_datetime': str(start_date),
                            })
                        if cal_events.stop_datetime != str(end_date):
                            update_vals.update({
                                'stop_datetime': str(end_date),
                            })
                    if update_vals:
                        cal_events.sudo().with_context(sync=True).write(
                            update_vals)
        return True
