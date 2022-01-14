# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, tools, _
from datetime import date, timedelta, datetime

from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = "mail.activity"

    activity_type_id = fields.Many2one(
        'mail.activity.type', 'Activity Type',
        domain="['|', ('res_model_id', '=', False), ('res_model_id', '=', res_model_id)]", ondelete='restrict')

    evaluation = fields.Selection(
        string='Evaluation',
        selection=[('negative', 'Negative'), ('indifferent', 'Indifferent'),
                   ('potential', 'Potential'), ('positive', 'Positive'),
                   ('very positive', 'Very positive')]
    )

    @api.model
    def _default_partners(self):
        """ When active_model is res.partner, the current partners
         should be attendees """
        partners = self.env.user.partner_id
        active_id = self._context.get('active_id')
        if self._context.get('active_model') == 'res.partner' and active_id:
            if active_id not in partners.ids:
                partners |= self.env['res.partner'].browse(active_id)
        return partners

    organisation_id = fields.Many2one(
        comodel_name='res.partner', string='Empresa',
        default=lambda x: x.default_organisation_id(),
    )
    seller_id = fields.Many2one(
        comodel_name='res.users', string='Vendedor')
    product_id = fields.Many2one(
        comodel_name='product.product', string='Id del producto')
    application_id = fields.Many2many(
        comodel_name='monolitic.client.segmentation',
        string='Segmentación de mercado')
    business_id = fields.Many2many(
        comodel_name='product.category', string='Segmentación de producto')
    represented_id = fields.Many2many(
        comodel_name='res.partner', string='Proveedor',
        domain=[('is_supplier', '=', True)],
        relation="partner_represented_ids",
        column1="partner_id", column2="represented_id")
    classification_id = fields.Many2one(
        comodel_name='monolitic.client.classification',
        string='Clasificación estratégica del cliente')
    comercial_activity = fields.Boolean(
        string='Actividad comercial', default=lambda x: x.is_comercial_user())
    start_date = fields.Datetime()
    duration = fields.Float(related=False)
    assistants_ids = fields.Many2many(comodel_name='res.partner',
                                      default=_default_partners, string="")
    place = fields.Char(string='')
    sub_user_ids = fields.Many2many(comodel_name='res.users',
                                    relation='mail_activity_sub_user_rel',
                                    column1='activity_id',
                                    column2='user_id',
                                    string='Companions',)

    sub_type_id = fields.Many2one(
        comodel_name='mail.activity.sub.type',
        string='SubType Activity')

    client_seg_ids = fields.Many2many(
        compute='_compute_client_seg_ids',
        comodel_name='monolitic.client.segmentation'
    )

    @api.depends('organisation_id')
    def _compute_client_seg_ids(self):
        domain = [('level_parents', '>=', 2)]
        for rec in self:
            if rec.organisation_id.segmentation_ids:
                domain = [(
                    'id', 'in', self.organisation_id.segmentation_ids.ids)]

            segmentations_obj = self.env[
                'monolitic.client.segmentation'].search(domain)
            rec.client_seg_ids = segmentations_obj.ids

    @api.onchange('activity_type_id')
    def _onchange_activity_type_id_custom(self):
        for rec in self:
            allow_ids = self.mapped('activity_type_id.sub_type_ids').ids
            if rec.sub_type_id and rec.sub_type_id.id not in allow_ids:
                rec.sub_type_id = False
            return {'domain': {'sub_type_id': [('id', 'in', allow_ids)]}}

    @api.constrains('sub_user_ids')
    def _check_sub_user_ids(self):
        for rec in self:
            if rec.user_id and rec.sub_user_ids:
                if rec.user_id.id in rec.sub_user_ids.ids:
                    raise ValidationError(_("You can not select same user as"
                                            " assigned to and as companion"))

    @api.onchange('sub_user_ids')
    def onchange_sub_user_ids(self):
        self.assistants_ids |= self.sub_user_ids.mapped('partner_id')

    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.start_date:
            self.date_deadline = self.start_date.date()
            self.calendar_event_id_start = self.start_date

    def action_open_calendar_event(self):
        self.ensure_one()
        self.action_save()
        res_id = self.calendar_event_id.id
        action = self.env.ref('calendar.action_calendar_event').read()[0]
        action['res_id'] = res_id
        return action

    def unlink(self):
        calendar_act_ids = self.filtered(lambda x: x.calendar_event_id)
        self.mapped('calendar_event_id').unlink()
        return super(MailActivity, self - calendar_act_ids).unlink()

    def action_save(self):
        self.ensure_one()
        if self.calendar_event_id:
            self.calendar_event_id.write({
                'name': self.summary or self.res_name,
                'start_date': self.start_date,
                'start': self.start_date,
                'duration': self.duration,
                'stop_date': self.start_date + timedelta(
                    hours=self.duration),
                'partner_ids': [(6, 0, self.assistants_ids.ids)],
                'location': self.place
            })

    def action_create_calendar_event(self):
        self.ensure_one()
        self = self.sudo()
        if not self.start_date:
            return super(MailActivity, self).action_create_calendar_event()
        stop_datetime = self.start_date + timedelta(hours=self.duration)
        values = {
            # 'activity_type_id': self.activity_type_id.id,
            'name': self.summary or self.res_name,
            'description': self.note and tools.html2plaintext(
                self.note).strip() or '',
            'activity_ids': [(6, 0, self.ids)],
            'start_date': self.start_date,
            'start': self.start_date,
            'stop_date': stop_datetime,
            'stop': stop_datetime,
            'location': self.place,
            'partner_ids': [(6, 0, self.assistants_ids.ids)],
            'res_model': self.env.context.get('default_res_model'),
            'res_id': self.env.context.get('default_res_id'),
        }
        calendar_id = self.env['calendar.event'].create(values)
        calendar_id.write({'duration': self.duration})
        self.write({'calendar_event_id': calendar_id.id})
        if (datetime.now() > self.start_date + timedelta(
                hours=self.duration)):
            self.summary += " " + self.start_date.strftime('%d-%m-%Y')
            return super(MailActivity, self).action_done()
        else:
            return

    @api.onchange('organisation_id')
    def _onchange_organisation_id(self):
        if self.organisation_id:
            self.classification_id = self.organisation_id.\
                strategic_classification
            ids = self.organisation_id.segmentation_ids.ids if \
                self.organisation_id.segmentation_ids else []
            self.application_id = [(6, 0, ids)]

            self.seller_id = False
            if self.organisation_id.user_id:
                self.seller_id = self.organisation_id.user_id[0].id
                return {'domain': {
                    'seller_id': [(
                        'id', 'in', self.organisation_id.user_id.ids)]
                }}
            else:
                return {'domain': {'seller_id': []}}
        else:
            self.classification_id = False
            self.application_id = False
            return {'domain': {'seller_id': []}}

    @api.onchange('comercial_activity')
    def _onchange_comercial_activity(self):
        for act in self:
            comercial_activity_default = act.is_comercial_user()
            if comercial_activity_default and not act.comercial_activity:
                act.organisation_id = False
                act.classification_id = False
                act.seller_id = False
                act.product_id = False
                act.application_id = False
                act.business_id = False
                act.represented_id = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                ids = rec.product_id.categ_id.ids if \
                    rec.product_id.categ_id else []
                rec.business_id = [(6, 0, ids)]
            else:
                rec.business_id = False

    @api.onchange('represented_id')
    def _onchange_represented_id(self):
        for rec in self:
            if not rec.business_id:
                if rec.represented_id:
                    ids = rec.represented_id[0].product_category_id.ids if \
                        rec.represented_id[0].product_category_id else []
                    rec.business_id = [(6, 0, ids)]
                else:
                    rec.business_id = False

    @api.onchange('business_id')
    def _onchange_business_id(self):
        res = {}
        res.update({
            'domain': {
                'business_id': [('complete_name', 'not ilike', 'All')],
            }
        })
        return res

    def default_organisation_id(self):
        context = dict(self._context or {})
        partner = False
        if ('default_res_model' in context
                and self._context['default_res_model'] == 'res.partner'):
            partner = self.env['res.partner'].browse([
                context.get('default_res_id', False)])

        elif ('default_res_model' in context
                and self._context['default_res_model'] == 'crm.lead'):
            partner = self.env['crm.lead'].browse([
                context.get('default_res_id', False)]).partner_id

        elif ('default_res_model' in context
                and self._context['default_res_model'] == 'sale.order'):
            partner = self.env['sale.order'].browse([
                context.get('default_res_id', False)]).partner_id

        elif ('default_res_model' in context
                and self._context['default_res_model'] == 'helpdesk.ticket'):
            partner = self.env['helpdesk.ticket'].browse([
                context.get('default_res_id', False)]).partner_id

        elif ('default_res_model' in context
                and self._context['default_res_model'] == 'project.task'):
            partner = self.env['project.task'].browse([
                context.get('default_res_id', False)]).partner_id

        elif ('default_res_model' in context
                and self._context['default_res_model'] == 'purchase.order'):
            partner = self.env['purchase.order'].browse([
                context.get('default_res_id', False)]).partner_id

        elif ('default_res_model' in context
                and self._context['default_res_model'] == 'account.move'):
            partner = self.env['account.move'].browse([
                context.get('default_res_id', False)]).partner_id

        elif ('default_res_model' in context
                and self._context['default_res_model'] == 'stock.picking'):
            partner = self.env['stock.picking'].browse([
                context.get('default_res_id', False)]).partner_id

        return partner or False

    def is_comercial_user(self):
        commercial_activity = False
        if self.env.user.is_delegate or self.env.user.is_commercial:
            commercial_activity = True
        return commercial_activity

    def _action_done(self, feedback=False, attachment_ids=None):
        res = super(MailActivity, self)._action_done(feedback=feedback)

        if (
            self.comercial_activity and
            self.activity_type_id.required_evaluation and
            not self.evaluation
        ):
            raise ValidationError(_(
                "The evaluation is required for this activity !"))
        return res

    def write(self, vals):
        res = super(MailActivity, self).write(vals)
        date_deadline = vals.get("date_deadline", False)
        start_date = vals.get("start_date", False)
        meeting_type_id = self.env.ref('mail.mail_activity_data_meeting').id
        for rec in self:
            if (
                date_deadline and not start_date
                and rec.activity_type_id.id == meeting_type_id
            ):
                raise UserError(_(
                    "This event must be moved through Calendar module!"))
        return res


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    sub_type_ids = fields.Many2many(
        comodel_name='mail.activity.sub.type',
        string="Allowed Sub types"
    )
    required_evaluation = fields.Boolean(default=False)


class MailActivitySubType(models.Model):
    _name = 'mail.activity.sub.type'
    _description = 'Activity sub type'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer()
    active = fields.Boolean(default=True)
