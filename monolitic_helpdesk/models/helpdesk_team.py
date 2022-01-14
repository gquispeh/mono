# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    is_ncc = fields.Boolean(string='Nonconforming Quality', default=False)
    is_author_customer = fields.Boolean(
        string='Is Author Customer', default=False)
    manager_id = fields.Many2many(
        'res.users', 'helpdesk_team_manager_rel', string='Manager')

    # Inherit by QubiQ to change original filters
    def action_view_all_rating(self):
        """ return the action to see all the rating about
            the tickets of the Team
        """
        domain = [
            ('parent_res_name', '=', self.name),
            ('rating', '!=', -1),
            ('res_model', '=', 'helpdesk.ticket'),
            ('consumed', '=', True)]
        #action = self.env.ref('rating.action_view_rating').read()[0]
        action = self.env["ir.actions.actions"]._for_xml_id("helpdesk.rating_rating_action_helpdesk")
        action['domain'] = domain
        return action
