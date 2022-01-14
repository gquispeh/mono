##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################

from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    code = fields.Char(
        string="Lead Number", required=True, default="/", readonly=True, copy=False
    )

    _sql_constraints = [
        ("crm_lead_unique_code", "UNIQUE (code)", _("The code must be unique!")),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        crm_type = ''
        if self._context.get('default_type', False):
            crm_type = self._context['default_type']

            for vals in vals_list:
                if vals.get('code', '/') == '/':
                    if crm_type == 'lead':
                        vals["code"] = self.env.ref(
                            "crm_lead_code.sequence_lead",
                            raise_if_not_found=False
                        ).next_by_id()
                    elif crm_type == 'opportunity':
                        vals["code"] = self.env.ref(
                            "crm_lead_code.sequence_opportunity",
                            raise_if_not_found=False
                        ).next_by_id()
        else:
            for vals in vals_list:
                if vals.get('code', '/') == '/':
                    vals["code"] = self.env.ref(
                        "crm_lead_code.sequence_lead",
                        raise_if_not_found=False
                    ).next_by_id()

        return super().create(vals_list)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()

        crm_type = self._context.get('default_type', '')
        if default is None:
            default = {}
        if crm_type == 'lead':
            default['code'] = self.env.ref(
                "crm_lead_code.sequence_lead",
                raise_if_not_found=False
            ).next_by_id()
        elif crm_type == 'opportunity':
            default['code'] = self.env.ref(
                "crm_lead_code.sequence_opportunity",
                raise_if_not_found=False
            ).next_by_id()

        return super(CrmLead, self).copy(default)

    def _convert_opportunity_data(self, customer, team_id=False):
        res = super(CrmLead, self)._convert_opportunity_data(customer, team_id)
        res['code'] = self.env.ref(
            "crm_lead_code.sequence_opportunity",
            raise_if_not_found=False
        ).next_by_id()

        return res
