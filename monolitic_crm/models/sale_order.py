# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models, fields

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    strategic_classification = fields.Many2one(
        comodel_name='monolitic.client.classification',
    )
    commercial_user_ids = fields.Many2many(
        comodel_name='res.users',
        compute='_compute_commercial_user_ids',
    )

    @api.depends('partner_id')
    def _compute_commercial_user_ids(self):
        domain = [('is_commercial', '=', True)]
        if self.partner_id:
            if self.partner_id.user_id:
                domain = [('id', 'in', self.partner_id.user_id.ids)]

        commercial_users_obj = self.env['res.users'].search(domain)
        self.commercial_user_ids = commercial_users_obj.ids

    '''
        Hard inherit because we can't change the dict before getting error
    '''
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        user_id = self.partner_id.user_id[0].id \
            if self.partner_id.user_id else False
        values = {
            'pricelist_id':
                self.partner_id.property_product_pricelist and
                self.partner_id.property_product_pricelist.id or False,
            'payment_term_id':
                self.partner_id.property_payment_term_id and
                self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'user_id': user_id,
            'strategic_classification':
                self.partner_id.strategic_classification,
        }
        if self.env['ir.config_parameter'].sudo().get_param(
                'sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(
                lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id

        if self.user_id.id == values.get('user_id'):
            del values['user_id']
        self._compute_commercial_user_ids()
        self.update(values)
