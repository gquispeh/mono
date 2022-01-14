from odoo import models, fields
import base64


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _create_partner_mandate(self):
        mandate_ids = self.env['account.banking.mandate']
        for bank in self.bank_ids:
            mandate_id = self.env['account.banking.mandate'].create({
                'format': 'sepa',
                'type': 'recurrent',
                'partner_bank_id': bank.id,
                'partner_id': self.id,
                'scheme': 'CORE',
                'recurrent_sequence_type': 'recurring',
                'signature_date': '2021-01-01',
            })
            mandate_ids += mandate_id

        report = self.env.ref(
            'account_banking_sepa_direct_debit.'
            'report_sepa_direct_debit_mandate'
        )

        for mandate_id in mandate_ids:
            mandate_id.validate()
            pdf = report._render_qweb_pdf(mandate_id.ids)
            mandate_id.scan = base64.b64encode(pdf[0])

    def create_partner_mandate(self):
        for partner in self:
            if partner.mandate_count == 0:
                partner.with_delay()._create_partner_mandate()
