# Copyright 2021 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ClientSegmentationWizard(models.TransientModel):
    _name = 'client.segmentation.wizard'
    _inherit = "category.levels.mixing"
    _description = 'Client Segmentation Levels Wizard'

    def get_object(self):
        return self.env['monolitic.client.segmentation']

    level_1 = fields.Many2one(comodel_name='monolitic.client.segmentation',
                              string="Unidad de negocio")
    level_2 = fields.Many2one(comodel_name='monolitic.client.segmentation',
                              string="Sector de mercado")
    level_3 = fields.Many2one(comodel_name='monolitic.client.segmentation',
                              string="Segmento de mercado")
    level_4 = fields.Many2one(comodel_name='monolitic.client.segmentation',
                              string="Subsegmento de mercado (nicho)")

    allow_categ_ids = fields.Many2many(
        comodel_name='monolitic.client.segmentation')

    init_category_id = fields.Many2one(
        comodel_name='monolitic.client.segmentation')

    def levels_contraints(self):
        return super(ClientSegmentationWizard, self).levels_contraints()

    def get_allow_partner_categs_activity(self, obj_id):
        allow_categ = []
        partner = False
        if obj_id.organisation_id:
            partner = obj_id.organisation_id
            if obj_id.organisation_id.parent_id:
                partner = obj_id.organisation_id.parent_id

        if partner:
            client_categ = partner.mapped('segmentation_ids')
            for categ in client_categ:
                allow_categ.append(categ.id)
                parent_id = categ.parent_id
                while parent_id:
                    allow_categ.append(parent_id.id)
                    parent_id = parent_id.parent_id
        return self.env['monolitic.client.segmentation'].\
            browse(allow_categ).filtered(lambda x: x.id != 1)

    def get_allow_partner_categs_crm(self, obj_id):
        allow_categ = []
        partner = False
        if obj_id.partner_id:
            partner = obj_id.partner_id
            if obj_id.partner_id.parent_id:
                partner = obj_id.partner_id.parent_id

        if partner:
            client_categ = partner.mapped('segmentation_ids')
            for categ in client_categ:
                allow_categ.append(categ.id)
                parent_id = categ.parent_id
                while parent_id:
                    allow_categ.append(parent_id.id)
                    parent_id = parent_id.parent_id
        return self.env['monolitic.client.segmentation'].\
            browse(allow_categ).filtered(lambda x: x.id != 1)

    def get_allow_partner_categs_sales(self, obj_id):
        allow_categ = []
        partner = False
        if obj_id.order_partner_id:
            partner = obj_id.order_partner_id
            if obj_id.order_partner_id.parent_id:
                partner = obj_id.order_partner_id.parent_id

        if partner:
            client_categ = partner.mapped('segmentation_ids')
            for categ in client_categ:
                allow_categ.append(categ.id)
                parent_id = categ.parent_id
                while parent_id:
                    allow_categ.append(parent_id.id)
                    parent_id = parent_id.parent_id
        return self.env['monolitic.client.segmentation'].\
            browse(allow_categ).filtered(lambda x: x.id != 1)

    def _compute_allow_categ_ids(self):
        model, res_id = self.get_model_and_id()
        obj_id = self.env[model].browse(res_id)
        if not obj_id:
            raise UserError(
                _("There is not a product select,"
                    " please click on Edit button again"))

        cat_obj = self.env['monolitic.client.segmentation']
        if model == 'account.invoice.line':
            self.allow_categ_ids = self.get_allow_partner_categs_crm(
                obj_id)
        elif model == 'sale.order.line':
            self.allow_categ_ids = self.get_allow_partner_categs_sales(
                obj_id)
        elif model == 'mail.activity':
            self.allow_categ_ids = self.get_allow_partner_categs_activity(
                obj_id)
        else:
            self.allow_categ_ids = cat_obj.search([
                ('parent_id', '=', False)
            ])

    @api.onchange('allow_categ_ids')
    def _onchange_allow_categ_ids(self):
        domain = [('parent_id', '=', False)]
        if not self.allow_categ_ids:
            model, res_id = self.get_model_and_id()
            obj_id = self.env[model].browse(res_id)
            if model in ['customer.prevision', 'account.invoice.line']:
                self.allow_categ_ids = self.get_allow_partner_categs_crm(
                    obj_id)
            elif model == 'sale.order.line':
                self.allow_categ_ids = self.get_allow_partner_categs_sales(
                    obj_id)
            elif model == 'mail.activity':
                self.allow_categ_ids = self.get_allow_partner_categs_activity(
                    obj_id)

        if self.allow_categ_ids:
            allow_categ = self.allow_categ_ids.filtered(
                lambda x: not x.parent_id and x.id != 1
            )
            if len(allow_categ) == 1:
                self.level_1 = allow_categ
                return {}
            domain += [('id', 'in', self.allow_categ_ids.ids)]
        return {'domain': {'level_1': domain}}

