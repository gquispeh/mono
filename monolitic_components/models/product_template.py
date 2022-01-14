# Copyright 2019 Jesus Ramoneda <jesus.ramoneda@qubiq.es>
# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models, api

import logging
_logger = logging.getLogger(__name__)


class MonoliticComponent(models.Model):
    _inherit = 'product.template'

    def _get_default_category_id(self):
        res = super(MonoliticComponent, self)._get_default_category_id()
        # Do not put ALL categ by default
        if res.id == 1:
            return False

        if self._context.get('default_is_component'):
            component_categ = self.env.ref(
                'monolitic_components.component_product_category')
            return component_categ.id
        else:
            return res
    
    def _default_responsible_id(self):
        return self.env['res.users'].search([('id', '=', 45)])
    
    purchase_date = fields.Date(string='Purchase Date')
    last_check_date = fields.Date(
        string='Last Check Date',
        default=fields.Date.context_today,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned User',
        tracking=True
    )
    responsable_id = fields.Many2one(
        comodel_name='res.partner',
        string="Assigned User",
        related="user_id.partner_id",
    )
    responsible_id = fields.Many2one(
        'res.users', string='Responsible', company_dependent=True, check_company=True,
        help="This user will be responsible of the next activities related to logistic operations for this product.", 
        default=_default_responsible_id,
    )

    component_type = fields.Many2one(
        comodel_name='product.component.type',
        string='Component Type',
        tracking=True
    )
    is_accounting_active = fields.Boolean(
        string='Is Accounting Active',
        default=True,
    )
    is_insured = fields.Boolean(
        string='Is Insured',
        tracking=True
    )

    type = fields.Selection(
        default='product',
    )

    component_location = fields.Selection(
        string='Component Location',
        selection=[('bcn_planta3', 'BCN-Planta3'),
                   ('bcn_planta2', 'BCN-Planta2'),
                   ('bcn_planta1', 'BCN-Planta1'),
                   ('bcn_planta0', 'BCN-Planta0'),
                   ('bilbao', 'Bilbao'),
                   ('madrid', 'Madrid'),
                   ('valencia', 'Valencia')],
        tracking=True)

    is_component = fields.Boolean(
        string='Componente', readonly=True, default=False
    )
    categ_id = fields.Many2one(
        'product.category',
        'Product Category',
        change_default=True,
        default=_get_default_category_id,
        help="Select category for the current product",
    )
    component_state = fields.Selection(
        string=u'State',
        selection=[('lost', 'Lost'), ('broken', 'Broken'),
                   ('stolen', 'Stolen'), ('obsolete', 'Obsolete'),
                   ('work', 'Operative')
                   ], tracking=True
    )
    attribute_line_ids = fields.One2many(
        readonly=False
    )
    attribute_ids = fields.Many2many(related="component_type.attributes_ids")

    component_quantity = fields.Integer(
        string='Quantity',
        tracking=True
    )

    @api.onchange('component_type')
    def onchange_component_type(self):
        attribute_list = self.component_type.attributes_ids.mapped('id')
        attr_line_list = [(5, 0, 0)]
        for attribute_id in attribute_list:
            attr_line_list.append((0, 0, {'attribute_id': attribute_id}))
        self.attribute_line_ids = attr_line_list

    @api.onchange('categ_id')
    def onchange_intrastat_id(self):
        self.intrastat_id = self.categ_id.intrastat_id
