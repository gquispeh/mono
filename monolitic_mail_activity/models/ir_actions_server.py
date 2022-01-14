# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    activity_type_id = fields.Many2one(
        string='Activity Type')
    activity_category = fields.Selection(
        related='activity_type_id.category', readonly=True)
    sub_type_id = fields.Many2one(
        comodel_name='mail.activity.sub.type',
        string='Activity Subtype',
    )
    activity_start_date_range = fields.Integer(string='Start Date In')
    activity_start_date_range_type = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], string='Start Date Type', default='days')
    duration = fields.Float(string='Duration')
    
    assistants_ids = fields.Many2many(string='Attendees', comodel_name='res.partner', relation='partner_assistants_ids', column1='partner_id', column2='action_id',)
    
    place = fields.Char(string='Place')
    sub_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='actions_server_sub_user_rel',
        column1='action_server_id',
        column2='user_id',
        string='Companions',
    )

    @api.onchange('activity_type_id')
    def _onchange_activity_type_id_custom(self):
        for rec in self:
            allow_ids = self.mapped('activity_type_id.sub_type_ids').ids
            if rec.sub_type_id and rec.sub_type_id.id not in allow_ids:
                rec.sub_type_id = False
            return {'domain': {'sub_type_id': [('id', 'in', allow_ids)]}}

    '''
        Total inherit because we can't change the creation otherwise
    '''
    @api.model
    def run_action_next_activity(self, action, eval_context=None):
        if not action.activity_type_id or not self._context.get(
                'active_id') or self._is_recompute(action):
            return False

        records = self.env[action.model_name].browse(self._context.get(
            'active_ids', self._context.get('active_id')))

        vals = {
            'summary': action.activity_summary or '',
            'note': action.activity_note or '',
            'activity_type_id': action.activity_type_id.id,
            'sub_type_id': action.sub_type_id.id or False,
            'duration': action.duration or 0.00,
            'place': action.place or '',
        }
        if action.assistants_ids:
            vals['assistants_ids'] = [(6, 0, action.assistants_ids.ids)]

        if action.sub_user_ids:
            vals['sub_user_ids'] = [(6, 0, action.sub_user_ids.ids)]

        if action.activity_date_deadline_range > 0:
            vals['date_deadline'] = fields.Date.context_today(
                action) + relativedelta(**{
                    action.activity_date_deadline_range_type:
                        action.activity_date_deadline_range
                })
        if action.activity_start_date_range > 0:
            vals['start_date'] = fields.Date.context_today(
                action) + relativedelta(**{
                    action.activity_start_date_range_type:
                        action.activity_start_date_range
                })
            vals['date_deadline'] = fields.Date.context_today(
                action) + relativedelta(**{
                    action.activity_start_date_range_type:
                        action.activity_start_date_range
                })

        for record in records:
            user = False
            if action.assistants_ids:
                for assistant in action.assistants_ids:
                    if assistant.user_ids:
                        user = assistant.user_ids[0]
                        break
            else:
                if action.activity_user_type == 'specific':
                    user = action.activity_user_id
                elif action.activity_user_type == 'generic' and \
                        action.activity_user_field_name in record:
                    user = record[action.activity_user_field_name]
            if user:
                vals['user_id'] = user.id
            record.activity_schedule(**vals)
        return False
