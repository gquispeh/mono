# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)


class MonoliticAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    @api.constrains('value_ids', 'attribute_id')
    def _check_valid_attribute(self):
        if any(line.value_ids > line.attribute_id.value_ids for line in self):
            raise ValidationError(
                _('You cannot use this attribute with the following value.'))
        return True

    @api.depends('attribute_id', 'value_ids')
    def name_get(self):
        result = []
        for record in self:
            if record.attribute_id and record.value_ids:
                name = record.attribute_id.name + ": " + ', '.\
                    join(record.value_ids.mapped('name'))
            else:
                name = record.attribute_id
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            op = '|'
            value = False
            if len(name.split(' ')) > 1:
                try:
                    # CAST FLOAT TO CHECK IF IS A NUMBER
                    float(name.split(' ')[-1])
                    value = name.split(' ')[-1].replace('.', '.')
                    name = ' '.join(name.split(' ')[:-1])
                    op = '&'
                except Exception:
                    pass
            name_2 = value or name
            domain = [
                op, ('value_ids', operator, name_2),
                ('attribute_id', 'ilike', name)
            ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        records = self.search(domain + args, limit=limit)
        return records.name_get()
