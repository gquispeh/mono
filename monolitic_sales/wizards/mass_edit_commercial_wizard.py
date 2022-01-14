# Copyright 2021 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import time
import dateutil

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class MassEditCommercialWizard(models.TransientModel):
    _name = 'mass.edit.commercial.wizard'
    _description = 'Mass Edit Commercial Wizard'

    previous_commercial_id = fields.Many2one(
        string='Previous Commercial',
        comodel_name='res.users',
        required=True,
    )
    new_commercial_id = fields.Many2one(
        string='New Commercial',
        comodel_name='res.users',
        required=True,
    )
    model_id = fields.Many2one(
        string='Document',
        comodel_name='ir.model',
        required=True,
    )
    field_id = fields.Many2one(
        string='Commercial Field',
        comodel_name='ir.model.fields',
        required=True,
    )
    model_name = fields.Char(
        related='model_id.model',
        string='Model Name',
        readonly=True,
        store=True,
    )
    filter_domain = fields.Char(
        string='Domain',
    )

    @api.onchange('model_id')
    def onchange_model_id(self):
        self.model_name = self.model_id.model

    @api.onchange('previous_commercial_id', 'field_id')
    def onchange_previous_commercial_id(self):
        if self.previous_commercial_id:
            self.filter_domain = \
                    '[["user_id","=",%d]]' % (self.previous_commercial_id.id)
        else:
            self.filter_domain = '[["user_id","=",False]]'

    def _get_eval_context(self):
        """ Prepare the context used when evaluating python code
            :returns: dict -- evaluation context given to safe_eval
        """
        return {
            'datetime': datetime,
            'dateutil': dateutil,
            'time': time,
            'uid': self.env.uid,
            'user': self.env.user,
        }

    def change_commercial_records(self):
        domain = []
        context = dict(self._context)
        if self.filter_domain:
            eval_context = self._get_eval_context()
            domain = safe_eval(self.filter_domain, eval_context)
            records = self.env[
                self.model_name].with_context(context).search(domain)
            if records:
                if self.field_id.ttype == 'many2one':
                    records.write({
                        self.field_id.name: self.new_commercial_id.id
                    })
                elif self.field_id.ttype == 'many2many':
                    records.write({
                        self.field_id.name:
                            [(3, self.previous_commercial_id.id)]
                    })
                    records.write({
                        self.field_id.name:
                            [(4, self.new_commercial_id.id)]
                    })
            else:
                raise ValidationError(_('No records found !'))
        else:
            raise ValidationError(_('No domain was selected !'))
