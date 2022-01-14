# © 2021 Albert Farrés <albert.farres@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import base64

import logging
_logger = logging.getLogger(__name__)


class CsvExportWizard(models.TransientModel):
    _name = 'csv.export.wizard'

    data = fields.Binary(string='File', readonly=True)
    name = fields.Char(string='File name', readonly=True)

    def action_csv_export(self):
        stock_objs = self.env['stock.picking'].browse(
            self._context['active_ids'])
        csv_txt = ""
        filename = "Stock_CSV_Export" + datetime.now().strftime(
            "_%d.%m.%Y.csv")
        for stock in stock_objs:

            client_code = ""
            if self.env.company.client_code:
                client_code = self.env.company.client_code

            stock_name = stock.name

            date = datetime.today().strftime("%d/%m/%y")

            service_type = ""
            if stock.carrier_id:
                if stock.carrier_id.name == 'IMPACK':
                    service_type = '24H'
                if stock.carrier_id.name == 'IMPACK/ECO':
                    service_type = 'ECO'
                if stock.carrier_id.name == 'IMPACK/PAL':
                    service_type = 'PAL'
                if stock.carrier_id.name == 'IMPACK10':
                    service_type = '10H'
                if stock.carrier_id.name == 'IMPACK14':
                    service_type = '14H'
                if stock.carrier_id.name == 'IMPACK8.30':
                    service_type = '830H'

            company_name = self.env.company.name

            company_address = ""
            if self.env.company.street:
                company_address = self.env.company.street

            company_city = ""
            if self.env.company.city:
                company_city = self.env.company.city

            parent_dest = ""
            if stock.partner_id.parent_id:
                parent_dest = stock.partner_id.parent_id.name

            address_dest = ""
            if stock.partner_id.street:
                address_dest = stock.partner_id.street

            phone_dest = ""
            if stock.partner_id.street:
                phone_dest = stock.partner_id.phone

            city_dest = ""
            if stock.partner_id.street:
                city_dest = stock.partner_id.city

            zip_dest = ""
            if stock.partner_id.zip:
                zip_dest = stock.partner_id.zip

            n_lumps = 0
            if stock.number_lumps:
                n_lumps = stock.number_lumps

            peso = 0.0
            if stock.impack_weight:
                peso = stock.impack_weight

            portes = 'P'

            stock_notes = ""
            if stock.note:
                stock_notes = stock.note

            saturday = "N"

            retorn = 'N'
            if stock.is_return:
                retorn = 'S'

            company_country = ""
            if self.env.company.country_id:
                company_country = self.env.company.country_id.name

            company_zip = ""
            if self.env.company.zip:
                company_zip = self.env.company.zip

            company_phone = ""
            if self.env.company.phone:
                company_phone = self.env.company.phone

            country_dest = ""
            if stock.partner_id.country_id:
                country_dest = stock.partner_id.country_id.name

            client_email = 'S'

            client_email2 = ''
            if stock.partner_id.email:
                client_email2 = stock.partner_id.email
            else:
                raise UserError("There is no email on delivery address!")

            sms_dest = 'N'

            email_dest = 'N'

            scan_alb_cli = 'N'

            row = [
                client_code, '', stock_name, date, service_type, company_name, company_address,
                company_city, parent_dest, address_dest, phone_dest, city_dest, zip_dest, '',
                str(n_lumps), '', '', '', str(peso), '', portes, '', '', stock_notes, saturday,
                retorn, company_country, company_zip, company_phone, country_dest, '', '',
                client_email, client_email, client_email2, sms_dest, '', email_dest, '', scan_alb_cli
            ]

            row = ["" if not x else x for x in row]
            csv_txt += '|'.join(row)
            csv_txt += "\r\n"

        new_file = base64.b64encode(csv_txt.encode('utf-8'))
        self.write({'data': new_file, 'name': filename})
        view = self.env.ref(
            'monolitic_stock.stock_csv_download_view')

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'view_mode': 'form',
            'target': 'new',
        }
