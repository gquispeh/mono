
from odoo import models
from odoo import tools
import pytz

import logging
_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    # Override due to some write inconsistencies

    def _sync_activities(self, fields):
        # Update activities
        for event in self:
            if event.activity_ids:
                activity_values = {}
                if 'name' in fields:
                    activity_values['summary'] = event.name
                if 'description' in fields:
                    activity_values['note'] = tools.plaintext2html(
                        event.description)
                if 'start' in fields:
                    # self.start is a datetime UTC
                    # *only when the event is not allday*
                    # activty.date_deadline is a date
                    # (No TZ, but should represent the day in which the user's
                    # TZ is)
                    # See 72254129dbaeae58d0a2055cba4e4a82cde495b7
                    # for the same issue, but elsewhere
                    deadline = event.start
                    user_tz = self.env.context.get('tz')
                    if user_tz and not event.allday:
                        deadline = pytz.UTC.localize(deadline)
                        deadline = deadline.astimezone(pytz.timezone(user_tz))
                    activity_values['date_deadline'] = deadline.date()

                    # MODIFIED QUBIQ
                    activity_values['start_date'] = deadline.date()
                    activity_values['duration'] = event.duration

                if 'user_id' in fields:
                    activity_values['user_id'] = event.user_id.id

                # MODIFIED QUBIQ
                activity_values['place'] = event.location
                activity_values['summary'] = event.name
                activity_values['assistants_ids'] = [
                    (6, 0, event.partner_ids.ids)]

                if activity_values.keys():
                    event.activity_ids.write(activity_values)
