# Copyright 2018 Xavier Jiménez <xavier.jimenez@qubiq.es>
# Copyright 2018 Sergi Oliva <sergi.oliva@qubiq.es>
# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# Copyright 2019 Aleix de la rubia <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
import base64
import csv
from io import StringIO

import logging
_logger = logging.getLogger(__name__)

LOGISTIC_TAG_DICT = {
    'Código de barras': 'barcode',
    'Código de barras desglosado': 'barcode_expanded',
    'Código QR': 'barcode_qr',
    'Etiqueta especial': 'special_tag',
    'Impresión manual x bultos': 'manual_printing_packages',
}


class ImportChartAccount(models.Model):
    _name = "import.contact"
    _description = "Import Contact"

    data = fields.Binary('File', required=True)
    name = fields.Char('Filename')
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    delimeter = fields.Char(
        string='Delimiter',
        default='|',
        help='Default delimiter ","',
    )
    type_contact = fields.Selection(
        string='Type',
        selection=[('customer', 'Customer'), ('contact', 'Contact')],
        default="customer")
    update = fields.Boolean()

    def _prepare_customer_data(self, values):
        # REPLACE FLOATS
        if values.get('company_credit_limit', False):
            c_credit_limit = values['company_credit_limit'].replace('.', '')
            c_credit_limit = c_credit_limit.replace(',', '.')
            values['company_credit_limit'] = float(c_credit_limit)
        if values.get('insurance_credit_limit', False):
            i_credit_limit = values['insurance_credit_limit'].replace('.', '')
            i_credit_limit = i_credit_limit.replace(',', '.')
            values['insurance_credit_limit'] = float(i_credit_limit)

        if values.get('logistic_customer_tag_type'):
            values['logistic_customer_tag_type'] = \
                LOGISTIC_TAG_DICT[values['logistic_customer_tag_type']]

        # SEARCH COUNTRY
        country = False
        if values.get("country_id", False):
            country = self.env['res.country'].search_read(
                [("code", "=", values['country_id'])], ['id'])
        if country:
            country = country[0].get('id', False)

        # SEARCH STATE
        state = False
        if values.get("state_id", False):
            state = self.env['res.country.state'].search_read(
                [("name", "ilike", values['state_id'])], ['id'])
            if state:
                state = state[0].get('id', False)
            elif country:
                state = self.env['res.country.state'].create({
                    'name': values['state_id'],
                    'country_id': country,
                    'code': values['state_id'],
                }).id

        values["country_id"] = country
        values["state_id"] = state

        # SEARCH PAYMENT
        if values.get("customer_payment_mode_id", False):
            payment = self.env['account.payment.mode'].with_context(
                lang='es_ES').search([(
                    "name", "=", values['customer_payment_mode_id'])])
            if payment:
                values["customer_payment_mode_id"] = payment.id
            else:
                values.pop("customer_payment_mode_id")
        if values.get("supplier_payment_mode_id", False):
            payment = self.env['account.payment.mode'].with_context(
                lang='es_ES').search([(
                    "name", "=", values['supplier_payment_mode_id'])])
            if payment:
                values["supplier_payment_mode_id"] = payment.id
            else:
                values.pop("supplier_payment_mode_id")

        # SEARCH PAYMENT TERM
        if values.get("property_payment_term_id", False):
            payment_term = self.env['account.payment.term'].with_context(
                lang='es_ES').search([(
                    "name", "=", values['property_payment_term_id'])])
            if payment_term:
                values["property_payment_term_id"] = payment_term.id
            else:
                values.pop("property_payment_term_id")

        if values.get("property_supplier_payment_term_id", False):
            payment_term = self.env['account.payment.term'].with_context(
                lang='es_ES').search([(
                    "name", "=", values['property_supplier_payment_term_id'])])
            if payment_term:
                values["property_supplier_payment_term_id"] = payment_term.id
            else:
                values.pop("property_supplier_payment_term_id")

        # SEARCH POSITION
        if values.get("property_account_position_id", False):
            fiscal_position = self.env['account.fiscal.position'].search(
                [("name", "=", values['property_account_position_id'])])
            if fiscal_position:
                values["property_account_position_id"] = fiscal_position.id
            else:
                values.pop("property_account_position_id")

        # SEARCH ACC BUY ACCOUNT STAND BY
        if values.get("property_account_receivable_id", False):
            acc_re = self.env['account.account'].search(
                [("code", "=", values['property_account_receivable_id'])])
            if acc_re:
                values["property_account_receivable_id"] = acc_re.id
            else:
                values.pop("property_account_receivable_id")

        # SEARCH ACC SEEL ACCOUNT STAND BY
        if values.get("property_account_payable_id", False):
            acc_buy = self.env['account.account'].search(
                [("code", "=", values['property_account_payable_id'])])
            if acc_buy:
                values["property_account_payable_id"] = acc_buy.id
            else:
                values.pop("property_account_payable_id")

        # SEARCH LANG
        if values.get("lang", False):
            lang = self.env['res.lang'].search([("name", "=", values['lang'])])
            if lang:
                values["lang"] = lang.code

        # SEARCH IBAN
        if "bank_ids.acc_number" in values.keys():
            if values["bank_ids.acc_number"] != "":
                banks_ids = {"acc_number": values["bank_ids.acc_number"]}
                values["bank_ids"] = [(0, 0, banks_ids)]
            values.pop("bank_ids.acc_number")

        # SEARCH PARTNER CATEGORY
        if values.get("category_id", False):
            if values['category_id']:
                categ_ids = []
                for name in values['category_id'].split(';'):
                    if name != '':
                        categ = self.env['res.partner.category'].with_context(
                            lang='es_ES').search([('name', '=', name)])
                        if categ:
                            categ_ids.append(categ.id)
                values['category_id'] = [(6, 0, categ_ids)]

        # SEARCH STRATEGIC CLASS
        if values.get('strategic_classification', False):
            classification_id = self.env[
                'monolitic.client.classification'].search([(
                    "name", "=", values['strategic_classification'])])
            if not classification_id:
                classification_id = self.env[
                    'monolitic.client.classification'].create({
                        'name': values["strategic_classification"]
                    })
            values["strategic_classification"] = classification_id.id

        # SEARCH PRODUCT CATEGORY
        if values.get("product_category_id", False):
            if values['product_category_id']:
                prod_obj = self.env['product.category'].search(
                    [('complete_name', '=', values['product_category_id'])])
                if prod_obj:
                    values['product_category_id'] = prod_obj.id
                else:
                    values.pop('product_category_id')

        # SEARCH COMMERCIAL
        if values.get("user_id", False):
            if values['user_id']:
                user_ids = []
                for name in values['user_id'].split(';'):
                    if name != '':
                        user = self.env['res.users'].search([
                            ('name', '=', name)
                        ])
                        if user:
                            user_ids.append(user.id)
                values['user_id'] = [(6, 0, user_ids)]

        # SEARCH PRICELIST
        if values.get("property_product_pricelist", False):
            if values['property_product_pricelist']:
                currency = self.env['res.currency'].search([(
                        'name', '=', values['property_product_pricelist'])])
                pricelist = self.env['product.pricelist'].search([
                    ('currency_id', '=', currency.id)], limit=1)
                if pricelist:
                    values['property_product_pricelist'] = pricelist.id
                else:
                    values.pop('property_product_pricelist')

        # SEARCH CURRENCY
        if values.get("property_purchase_currency_id", False):
            if values['property_purchase_currency_id']:
                currency = self.env['res.currency'].search(
                    [('name', '=', values['property_purchase_currency_id'])])
                if currency:
                    values['property_purchase_currency_id'] = currency.id
                else:
                    values.pop('property_purchase_currency_id')

        # SEARCH CARRIER
        if values.get("property_delivery_carrier_id", False):
            if values['property_delivery_carrier_id']:
                carrier = self.env['delivery.carrier'].with_context(
                    lang='es_ES').search([(
                        'name', '=', values['property_delivery_carrier_id'])])
                if carrier:
                    values['property_delivery_carrier_id'] = carrier.id
                else:
                    values.pop('property_delivery_carrier_id')

        if values.get("delivery_conditions_id", False):
            if values['delivery_conditions_id']:
                delivery_cond = self.env['stock.delivery.condition'].with_context(
                    lang='es_ES').search([(
                        'name', '=', values['delivery_conditions_id'])])
                if delivery_cond:
                    values['delivery_conditions_id'] = delivery_cond.id
                else:
                    values.pop('delivery_conditions_id')

        # SEARCH TEAM ID
        if values.get("team_id", False):
            if values['team_id']:
                team = self.env['crm.team'].with_context(
                    lang='es_ES').search([(
                        'name', '=', values['team_id'])])
                if team:
                    values['team_id'] = team.id
                else:
                    values.pop('team_id')

        # SEARCH MARKET SEGMENTATION
        if values.get("segmentation_ids", False):
            if values['segmentation_ids']:
                segmentations = []
            for name in values['segmentation_ids'].split(';'):
                if name != '':
                    segmentation = self.env[
                        'monolitic.client.segmentation'].search([(
                            'complete_name', '=', name)])
                    if segmentation:
                        segmentations.append(segmentation.id)
            values['segmentation_ids'] = [(6, 0, segmentations)]

        # SEARCH ACTIVITY
        if values.get("activity_id"):
            if values['activity_id']:
                activities = []
                for name in values['activity_id'].split(';'):
                    if name != '':
                        activity = self.env[
                            'res.partner.activity'].with_context(
                                lang='es_ES').search([('name', '=', name)])
                        if activity:
                            activities.append(activity.id)
                values['activity_id'] = [(6, 0, activities)]

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

        return values

    def _prepare_contact_data(self, values):
        # SEARCH COUNTRY
        country = False
        if values.get("country_id", False):
            country = self.env['res.country'].search_read(
                [("code", "=", values['country_id'])], ['id'])
        if country:
            country = country[0].get('id', False)

        # SEARCH STATE
        state = False
        if values.get("state_id", False):
            state = self.env['res.country.state'].search_read(
                [("name", "ilike", values['state_id'])], ['id'])
            if state:
                state = state[0].get('id', False)
            elif country:
                state = self.env['res.country.state'].create({
                    'name': values['state_id'],
                    'country_id': country,
                    'code': values['state_id'],
                }).id
        values["country_id"] = country
        values["state_id"] = state

        # SEARCH LANG
        if values.get("lang", False):
            lang = self.env['res.lang'].search([("name", "=", values['lang'])])
            if lang:
                values["lang"] = lang.code

        # SEARCH FOR PARENT
        if values.get("parent_id", False):
            parent_id = self.env['res.partner'].with_context(
                active_test=False).search([
                    ('ref', '=', values['parent_id']),
                    ('parent_id', '=', False)
                ])
            if parent_id:
                values['parent_id'] = parent_id.id
            else:
                raise UserError("No parent with code %s found" %
                                values['parent_id'])

        # SEARCH FOR JOB POSITIONS (M2M ON MONOLITIC)
        if values.get("function"):
            if values['function']:
                function_list = []
                for name in values['function'].split(';'):
                    if name != '':
                        function_obj = self.env[
                            'res.partner.job'].with_context(
                                lang='es_ES').search([('name', '=', name)])
                        if not function_obj:
                            function_obj = self.env[
                                'res.partner.job'].create({
                                    'name': name
                                })
                        function_list.append(function_obj.id)
                values['function'] = [(6, 0, function_list)]

        # SEARCH FOR INCLUDE ON MAILING
        if values.get("include_on_mailing"):
            if values['include_on_mailing']:
                include_mailing_list = []
                for name in values['include_on_mailing'].split(';'):
                    if name != '':
                        mailing_opt = self.env[
                            'contact.mail.options'].with_context(
                                lang='es_ES').search([('name', '=', name)])
                        if not mailing_opt:
                            mailing_opt = self.env[
                                'contact.mail.options'].create({
                                    'name': name
                                })
                        include_mailing_list.append(mailing_opt.id)
                values['include_on_mailing'] = [(6, 0, include_mailing_list)]

        # SEARCH FOR EXCLUDE ON MAILING
        if values.get("exclude_on_mailing"):
            if values['exclude_on_mailing']:
                exclude_mailing_list = []
                for name in values['exclude_on_mailing'].split(';'):
                    if name != '':
                        mailing_opt = self.env[
                            'contact.mail.options'].with_context(
                                lang='es_ES').search([('name', '=', name)])
                        if not mailing_opt:
                            mailing_opt = self.env[
                                'contact.mail.options'].create({
                                    'name': name
                                })
                        exclude_mailing_list.append(mailing_opt.id)
                values['exclude_on_mailing'] = [(6, 0, exclude_mailing_list)]

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

        return values

    def _create_res_partner(self, values, update):
        partner_obj = self.env['res.partner']
        partner = partner_obj.with_context(
            active_test=False).search([('ref', '=', values['ref'])])
        partner = partner[0] if partner else partner

        if self.type_contact == "customer":
            partner_vals = self._prepare_customer_data(values)
        elif self.type_contact == "contact":
            partner_vals = self._prepare_contact_data(values)
        if not partner_vals:
            raise UserError("Error preparing customer/contact data")

        if 'credit_policy_state_name' in partner_vals:
            partner_vals.pop('credit_policy_state_name')

        if partner:
            if not update:
                _logger.info("Partner already exists: %s", partner.name)
                return False
            else:
                _logger.info("====== PARTNER VALS UPD =======")
                _logger.info(partner_vals)
                partner.write(partner_vals)
                _logger.info("Updated partner: %s", partner.name)
        else:
            _logger.info("====== PARTNER VALS CREATE =======")
            _logger.info(partner_vals)
            partner = partner.create(partner_vals)
            _logger.info("Created partner: %s", partner.name)

        if values.get("create_date", False):
            self._cr.execute("""
                UPDATE res_partner
                SET create_date = %s
                WHERE id = %s
            """, (values['create_date'], str(partner.id)))
            created_message = self.env['mail.message'].sudo().search([
                ('res_id', '=', partner.id),
                ('model', '=', 'res.partner'),
            ], order='id asc', limit=1)
            if created_message:
                self._cr.execute("""
                    UPDATE mail_message
                    SET date = %s
                    WHERE id = %s
                """, (values['create_date'], str(created_message.id)))
        return True

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
        reader = csv.reader(
            file_input, delimiter=delimeter, lineterminator='\r\n')
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
            if temp == '\ufeff"ref"':
                temp = 'ref'
            keys.append(temp)
        _logger.info('The keys of the file are: ')
        _logger.info(keys)
        del reader_info[0]
        values = {}
        for i in range(len(reader_info)):
            if reader_info[i]:
                # Don't read rows that start with ( , ' ' or are empty
                if not (reader_info[i][0] == '' or reader_info[i][0][0] == '('
                        or reader_info[i][0][0] == ' '):
                    field = reader_info[i]
                    values = dict(zip(keys, field))
                    self.with_delay()._create_res_partner(values, self.update)

        return {'type': 'ir.actions.act_window_close'}

    def delete_partners(self):
        partners = self.env['res.partner'].with_context(
            active_test=False).search([('user_ids', '=', False)])
        for rec in partners:
            if rec.ticket_count == 0:
                rec.with_delay().unlink()
