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

MODEL_FIELD_MAPPER = {
    'res.partner': 'ref',
    'account.invoice': 'number',
    'crm.lead': 'code',
    'product.template': 'default_code',
    'sale.order': 'name',
    'stock.picking': 'name',
    'mrp.production': 'name',
    'crm.claim.ept': 'code',
    'claim.line.ept': 'unique_code',
}


class ImportActivities(models.Model):
    _name = 'import.activity'
    _description = 'Import Activities'

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    delimeter = fields.Char('Delimiter', default='|',
                            help='Default delimiter "|"')

    def _prepare_activity_data(self, values):
        # Convert booleans
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

        # Activity type
        if values.get("activity_type_id", False):
            activity_type = self.env['mail.activity.type'].with_context(
                lang='es_ES').search([
                    ('name', '=', values['activity_type_id'])])
            if activity_type:
                values.update({'activity_type_id': activity_type.id})
            else:
                raise UserError(_(
                    "Activity type %s does not exist."
                ) % values['activity_type_id'])

        # Activity subtype
        if values.get("sub_type_id", False):
            sub_type = self.env['mail.activity.sub.type'].with_context(
                lang='es_ES').search([('name', '=', values['sub_type_id'])])
            if sub_type:
                values.update({'sub_type_id': sub_type.id})
            else:
                raise UserError(_(
                    "Activity subtype %s does not exist."
                ) % values['sub_type_id'])

        # Date deadline
        # if values.get("date_deadline", False):
        #     date_deadline = datetime.datetime.strptime(
        #         values['date_deadline'], '%d/%m/%Y').strftime('%Y-%m-%d')
        #     values.update({'date_deadline': date_deadline})
        # else:
        #     del values['date_deadline']

        # User + Assistants
        assistants_list = []
        if values.get("user_id", False):
            user = self.env['res.users'].with_context(
                active_test=False).search([(
                    'name', '=', values['user_id'])])
            if user:
                values.update({'user_id': user.id})
                assistants_list.append(user.partner_id.id)
            else:
                raise UserError(_(
                    "User %s does not exist.") % values['user_id']
                )

        # Subusers + Assistants
        if values.get("sub_user_ids", False):
            users = values['sub_user_ids'].split(';')
            user_list = []
            for user in users:
                user = self.env['res.users'].with_context(
                    active_test=False).search([('name', '=', user)])
                if user:
                    user_list.append(user.id)
                    assistants_list.append(user.partner_id.id)
                else:
                    raise UserError(_(
                        "User %s does not exist.") % user)
            if user_list:
                values.update({'sub_user_ids': [(6, 0, user_list)]})

        values.update({'assistants_ids': [(6, 0, assistants_list)]})

        # Aplication - Market segmentation
        if values.get("application_id", False):
            applications = values['application_id'].split(',')
            application_list = []
            for application in applications:
                final_name = application.replace('/', ' / ')
                application_obj = self.env[
                    'monolitic.client.segmentation'].search([(
                        'complete_name', '=', final_name)])
                if application_obj:
                    application_list.append(application_obj.id)
            if application_list:
                values.update({'application_id': [(6, 0, application_list)]})
            else:
                del values['application_id']

        # Product
        if values.get("product_id", False):
            product = self.env['product.product'].search(
                [('default_code', '=', values['product_id'])]
            )
            if product:
                values.update({'product_id': product.id})
            else:
                raise UserError(_(
                    "Product %s does not exist.") % values['product_id'])

        # Business - Product segmentation
        if values.get("business_id", False):
            businesses = values['business_id'].split(',')
            business_list = []
            for business in businesses:
                business_obj = self.env['product.category'].search(
                    [('complete_name', '=', business.replace('/', ' / '))])
                if business_obj:
                    business_list.append(business_obj.id)
            if business_list:
                values.update({'business_id': [(6, 0, business_list)]})
            else:
                del values['business_id']

        # Seller
        if values.get("seller_id", False):
            seller = self.env['res.users'].with_context(
                active_test=False).search([
                    ('name', '=', values['seller_id'])])
            if seller:
                values.update({'seller_id': seller.id})
            else:
                raise UserError(_(
                    "Seller %s does not exist."
                ) % values['seller_id'])

        # Organisation
        if values.get("organisation_id", False):
            organisation = self.env['res.partner'].with_context(
                active_test=False).search([
                    ('ref', '=', values['organisation_id'])])
            if organisation:
                values.update({'organisation_id': organisation.id})
            else:
                raise UserError(_(
                    "Organisation %s does not exist."
                ) % values['organisation_id'])

        # Represented
        if values.get("represented_id", False):
            suppliers = values['represented_id'].split(';')
            supplier_list = []
            for supplier in suppliers:
                supplier_obj = self.env['res.partner'].with_context(
                    active_test=False).search([(
                        'ref', '=', values['represented_id'])])
                if supplier_obj:
                    supplier_list.append(supplier_obj.id)
                else:
                    raise UserError(_(
                        "Supplier %s does not exist."
                    ) % values['represented_id'])

            if supplier_list:
                values.update({'represented_id': [(6, 0, supplier_list)]})

        # Evaluation
        if values.get("evaluation", False):
            if values['evaluation'] == 'Negative':
                values['evaluation'] = 'negative'
            if values['evaluation'] == 'Indiferent':
                values['evaluation'] = 'indiferent'
            if values['evaluation'] == 'Potential':
                values['evaluation'] = 'potential'
            if values['evaluation'] == 'Positive':
                values['evaluation'] = 'positive'
            if values['evaluation'] == 'Very positive':
                values['evaluation'] = 'very positive'

        if values.get("res_model", False) and values.get("res_id", False):
            domain = (
                MODEL_FIELD_MAPPER[values['res_model']], '=', values['res_id']
            )
            res_obj = self.env[values['res_model']].with_context(
                active_test=False).search([domain])
            if res_obj:
                values.update({
                    'res_id':  res_obj.id,
                    'res_model_id': self.env[
                        'ir.model']._get(values['res_model']).id,
                })
            else:
                raise UserError(_("Res ID not found %s!") % values['res_id'])
        else:
            raise UserError(_("You must set a res_model and res_id!"))

        return values

    def _create_activity(self, values):
        activity_values = self._prepare_activity_data(values)
        # Get certain values to not create activity with them
        # and do some logic after
        create_date = values['create_date']
        create_user = values['create_user']
        del values['create_date']
        del values['create_user']

        done = values['done']
        del values['done']
        date_done = False
        if 'date_done' in values:
            date_done = values['date_done']
            del values['date_done']
        feedback = ''
        if 'feedback' in values:
            feedback = values['feedback']
            del values['feedback']

        _logger.info('VALS')
        _logger.info(activity_values)
        activity_obj = self.env['mail.activity'].sudo().create(activity_values)

        if create_date:
            user = self.env.user
            if create_user:
                result = self.env['res.users'].with_context(
                    active_test=False).search([(
                        'name', '=', create_user)])
                if result:
                    user = result
            user_obj = user

            self._cr.execute("""
                UPDATE mail_activity
                SET create_date = %s, create_uid = %s
                WHERE id = %s
            """, (create_date, user_obj.id, str(activity_obj.id)))

        if done:
            message = activity_obj.with_user(activity_obj.user_id.id)._action_done(feedback)
            activity_obj.write({
                'done': done,
                'date_done': date_done
            })
            message[0].write({
                'date': date_done
            })

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
            if temp == '\ufeff"activity_type_id"':
                temp = 'activity_type_id'
            keys.append(temp)
        del reader_info[0]

        values = {}

        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self.with_delay(priority=1)._create_activity(values)

        return {'type': 'ir.actions.act_window_close'}
