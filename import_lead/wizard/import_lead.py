# Copyright 2020 Xavier Jiménez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, exceptions, _
from odoo.exceptions import UserError

import base64
import csv
import datetime
from io import StringIO

import logging
_logger = logging.getLogger(__name__)


class ImportLead(models.Model):
    _name = 'import.lead'
    _description = 'Import Leads'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimiter', default='|',
                            help='Default delimiter "|"')
    update = fields.Boolean()

    '''
        Function to assign not direct mapping data.

        :param values: Dict with the values to import.

        :return Dict with the correct mapping.
    '''
    def _prepare_lead_data(self, values):

        # CONVERT BOOLS AND DELETE EMPTYS
        keys_miss_list = []
        for k, v in values.items():
            if v == "":
                keys_miss_list.append(k)
            elif v in ["True", "False"]:
                values[k] = eval(v)
            elif v == "Sí":
                values[k] = True
            elif v == "No":
                values[k] = False

        for key in keys_miss_list:
            values.pop(key)

        # CONVERT DATES
        # date_open = False
        # if values.get("date_open", False):
        #     date_open = datetime.datetime.strptime(
        #         values['date_open'], '%d/%m/%Y').strftime('%Y-%m-%d')
        # date_closed = False
        # if values.get("date_closed", False):
        #     date_closed = datetime.datetime.strptime(
        #         values['date_closed'], '%d/%m/%Y').strftime('%Y-%m-%d')
        # date_deadline = False
        # if values.get("date_deadline", False):
        #     date_deadline = datetime.datetime.strptime(
        #         values['date_deadline'], '%d/%m/%Y').strftime('%Y-%m-%d')
        # date_previous_stage = False
        # if values.get("date_previous_stage", False):
        #     date_previous_stage = datetime.datetime.strptime(
        #         values['date_previous_stage'], '%d/%m/%Y').strftime('%Y-%m-%d')
        # date_next_stage = False
        # if values.get("date_next_stage", False):
        #     date_next_stage = datetime.datetime.strptime(
        #         values['date_next_stage'], '%d/%m/%Y').strftime('%Y-%m-%d')

        # CONVERT FLOATS
        if values.get('probability', False):
            probability = values['probability'].replace('.', '')
            probability = probability.replace(',', '.')
            values['probability'] = float(probability)
        if values.get('expected_revenue', False):
            p_revenue = values['expected_revenue'].replace('.', '')
            p_revenue = p_revenue.replace(',', '.')
            values['expected_revenue'] = float(p_revenue)
        if values.get('competence_target', False):
            c_target = values['competence_target'].replace('.', '')
            c_target = c_target.replace(',', '.')
            values['competence_target'] = float(c_target)

        # SEARCH PARTNER
        partner = False
        if values.get("partner_id", False):
            partner = self.env['res.partner'].with_context(
                active_test=False).search_read([(
                    'ref', '=', values['partner_id'])], ['id'])
            if partner:
                partner = partner[0].get('id', False)

        # SEARCH USER
        user = False
        if values.get("user_id", False):
            user = self.env['res.users'].with_context(
                active_test=False).search_read([(
                    'name', '=', values['user_id'])], ['id'])
            if user:
                user = user[0].get('id', False)

        # SEARCH CAMPAIGN
        campaign = False
        if values.get("campaign_id", False):
            campaign_obj = self.env['utm.campaign']
            campaign = campaign_obj.search_read([
                ('name', '=', values['campaign_id'])], ['id'])
            if campaign:
                campaign = campaign[0].get('id', False)
            else:
                campaign = campaign_obj.create({
                    'name': values['campaign_id'],
                }).id

        # SEARCH MEDIA
        medium = False
        if values.get("medium_id", False):
            medium_obj = self.env['utm.medium']
            medium = medium_obj.search_read([
                ('name', '=', values['medium_id'])], ['id'])
            if medium:
                medium = medium[0].get('id', False)
            else:
                medium = medium_obj.create({
                    'name': values['medium_id'],
                }).id

        # SEARCH SOURCE
        source = False
        if values.get("source_id", False):
            source_obj = self.env['utm.source']
            source = source_obj.search_read([
                ('name', '=', values['source_id'])], ['id'])
            if source:
                source = source[0].get('id', False)
            else:
                source = source_obj.create({
                    'name': values['source_id'],
                }).id

        # SEARCH ASSEMBLER
        assembler = False
        if values.get("assembler_id", False):
            assembler_obj = self.env['res.partner']
            assembler = assembler_obj.search_read([
                ('ref', '=', values['assembler_id'])], ['id'])
            if assembler:
                assembler = assembler[0].get('id', False)

        # SEARCH ENGINEER
        engineer = False
        if values.get("engineer_id", False):
            engineer_obj = self.env['res.partner']
            engineer = engineer_obj.search_read([
                ('ref', '=', values['engineer_id'])], ['id'])
            if engineer:
                engineer = engineer[0].get('id', False)

        # SEARCH DEPARTMENT
        hr_department = False
        if values.get("hr_department_id", False):
            hr_department_obj = self.env['hr.department']
            hr_department = hr_department_obj.search_read([
                ('name', '=', values['hr_department_id'])], ['id'])
            if hr_department:
                hr_department = hr_department[0].get('id', False)

        # SEARCH SUPPLIER
        supplier = False
        if values.get("supplier_id", False):
            supplier_obj = self.env['res.partner']
            supplier = supplier_obj.with_context(
                active_test=False).search_read([(
                    'ref', '=', values['supplier_id'])], ['id'])
            if supplier:
                supplier = supplier[0].get('id', False)

        # SEARCH CLOSING ACTION
        closing_action = False
        if values.get("closing_action_id", False):
            closing_action_obj = self.env['crm.closing.action']
            closing_action = closing_action_obj.search_read([
                ('name', '=', values['closing_action_id'])], ['id'])
            if closing_action:
                closing_action = closing_action[0].get('id', False)

        # SEARCH COUNTRY
        country = False
        if values.get("country_id", False):
            country = self.env['res.country'].search_read(
                [("code", "=", values['country_id'])], ['id'])
        if country:
            country = country[0].get('id', False)

        # SEARCH STATE / COMMERCIAL ZONE
        state = False
        commercial_zone = False
        if values.get("state_id", False):
            state = self.env['res.country.state'].search([(
                "name", "ilike", values['state_id'])], order='id asc', limit=1)
            if state:
                commercial_zone = state.commercial_zone_id.id
                state = state.id
            elif country:
                state = self.env['res.country.state'].create({
                    'name': values['state_id'],
                    'country_id': country,
                    'code': values['state_id'],
                }).id

        # SEARCH LOST REASON
        lost_reason = False
        if values.get("lost_reason", False):
            lost_reason = self.env['crm.lost.reason'].search_read(
                [("name", "=", values['lost_reason'])], ['id'])
            if lost_reason:
                lost_reason = lost_reason[0].get('id', False)

        # SEARCH STAGE
        stage = 1
        if values.get("stage_id", False):
            stage = self.env['crm.stage'].with_context(
                    lang='es_ES'
                ).search_read([("name", "=", values['stage_id'])], ['id'])
            if stage:
                stage = stage[0].get('id', False)

        # SEARCH TAGS
        tag_ids = []
        if values.get("tags_id"):
            tags = values['tags_id'].split(',')
            for tag in tags:
                tag_obj = self.env['crm.tag'].search([('name', '=', tag)])
                if tag_obj:
                    tag_ids.append(tag_obj.id)

        # COMPOSE DICT
        values["partner_id"] = partner
        values["user_id"] = user
        values["closing_action_id"] = closing_action
        values["supplier_id"] = supplier
        values["hr_department_id"] = hr_department
        values["engineer_id"] = engineer
        values["assembler_id"] = assembler
        values["campaign_id"] = campaign
        values["medium_id"] = medium
        values["source_id"] = source
        values["function"] = ""
        # values["date_open"] = date_open
        # values["date_closed"] = date_closed
        # values["date_deadline"] = date_deadline
        # values["date_previous_stage"] = date_previous_stage
        # values["date_next_stage"] = date_next_stage
        values["state_id"] = state
        values["commercial_zone_id"] = commercial_zone
        values["country_id"] = country
        values["lost_reason"] = lost_reason
        values["stage_id"] = stage
        values["tag_ids"] = [(6, 0, tag_ids)]

        if values.get("name", False):
            values["name"] = values["name"]
        else:
            values["name"] = values["partner_name"]

        return values

    '''
        Function to create or write the crm lead / opp.

        :param values: Dict with the values to import.
    '''
    def _create_crm_lead(self, values, update):
        lead_obj = self.env['crm.lead']
        lead = lead_obj.with_context(active_test=False).search([
            ('code', '=', values['code'])])

        # Get status to update OPPN after inserting data
        lead_status = values.get("status")
        del values["status"]

        lead_vals = self._prepare_lead_data(values)

        _logger.info('=== LEAD VALS ===')
        _logger.info(lead_vals)

        if not lead_vals:
            raise UserError("Error preparing Lead/OPPN data")

        if lead:
            if not update:
                return "Lead/OPPN %s already exists" % lead.code
            else:
                lead.write(lead_vals)
                if lead_status == 'Perdida':
                    lost_reason = \
                        lead.lost_reason.id if lead.lost_reason else False
                    lead.action_set_lost(lost_reason=lost_reason)
                elif lead_status == 'Stand by':
                    lead.action_set_stand_by()
                elif lead_status == 'Ganada':
                    lead.action_set_won_rainbowman()

                return "Lead/OPPN updated: %s" % lead.code
        else:
            lead = lead_obj.create(lead_vals)
            lead.write({
                'date_open': lead_vals['date_open'],
            })
            if lead_status == 'Perdida':
                lost_reason = \
                    lead.lost_reason.id if lead.lost_reason else False
                lead.action_set_lost(lost_reason=lost_reason)
            elif lead_status == 'Stand by':
                lead.action_set_stand_by()
            elif lead_status == 'Ganada':
                lead.action_set_won_rainbowman()

            return "Lead/OPPN created: %s" % lead.code

    '''
        Function to read the csv file and convert it to a dict.

        :return Dict with the columns and its value.
    '''
    def action_import(self):
        """Load Inventory data from the CSV file."""
        if not self.data:
            raise exceptions.Warning(_("You need to select a file!"))
        # Decode the file data
        data = base64.b64decode(self.data).decode('utf-8')
        file_input = StringIO(data)
        file_input.seek(0)
        reader_info = []
        if self.delimeter:
            delimeter = str(self.delimeter)
        else:
            delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter,
                            lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file!"))
        keys = reader_info[0]

        # Get column names
        keys_init = reader_info[0]
        keys = []
        for k in keys_init:
            temp = k.replace(' ', '_')
            if temp == '\ufeff"code"':
                temp = 'code'
            keys.append(temp)
        del reader_info[0]
        _logger.info('The keys of the file are: ')
        _logger.info(keys)

        values = {}

        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self.with_delay()._create_crm_lead(values, self.update)

        return {'type': 'ir.actions.act_window_close'}
