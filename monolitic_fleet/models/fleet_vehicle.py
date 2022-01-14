# Copyright 2019 Aleix De la Rubia Campamà <aleix.delarubia@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _description = 'Vehicle'

    car_consumption = fields.Float(string='Car consumption')
    contracted_km = fields.Float(string='Contracted kilometers')

    def write(self, vals):
        user_fleet_group = 'fleet.fleet_group_manager'
        if not self.env.user.has_group(user_fleet_group):
            if len(vals) != 1 or 'driver_id' not in vals:
                raise UserError(_(
                    'You cannot modify vehicle information, '
                    'please contact with an Administrator.'))
        return super(FleetVehicle, self).write(vals)
