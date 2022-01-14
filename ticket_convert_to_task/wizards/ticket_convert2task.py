# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class TicketConvert2Task(models.TransientModel):
    _name = "ticket.convert2task"
    _description = "Ticket Convert To Task"

    @api.model
    def default_get(self, fields):
        result = super(TicketConvert2Task, self).default_get(fields)
        active_id = self.env.context.get('active_id')

        if active_id:
            ticket_obj = self.env['helpdesk.ticket'].browse([active_id])
            result['ticket_id'] = active_id
            result['name'] = ticket_obj.name
            result['user_id'] = self.env.uid
        return result

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
    )
    name = fields.Char(
        string="Ticket Name",
        required=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string="Assign To",
        tracking=True,
    )

    def ticket_convert2task(self):
        self.ensure_one()
        ticket = self.ticket_id
        task_values = {
            'name': self.name,
            'project_id': ticket.project_id.id,
            'user_id': self.user_id.id,
            'description': ticket.description,
            'ticket_id': ticket.id,
        }
        task = self.env['project.task'].create(task_values)
        # Move the mail thread and attachments
        ticket.message_change_thread(task)
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'helpdesk.ticket'),
            ('res_id', '=', ticket.id)
        ])
        attachments.write({
            'res_model': 'project.task', 'res_id': task.id
        })
        # Archive the ticket and send the timesheets to the new Task
        ticket.write({
            'active': False,
            'task_id': task.id,
        })
        # Return the action to go to the form view of the new Task
        view = self.env.ref('project.view_task_form2')

        return {
            'name': 'Task created',
            'view_mode': 'form',
            'view_id': view.id,
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'res_id': task.id,
            'context': self.env.context
        }
