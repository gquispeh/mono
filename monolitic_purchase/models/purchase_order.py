# Copyright 2019 Xavier Jimenez <xavier.jimenez@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    related_sale_orders = fields.Many2many(
        'sale.order',
        string='Related Sale Orders',
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        hide = [
            'price_unit'
        ]
        res = super(PurchaseOrder, self).fields_get(allfields, attributes=attributes)
        for field in hide:
            if field in res:
                res[field]['searchable'] = False
                res[field]['sortable'] = False
                res[field]['exportable'] = False
        return res

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        send_alert = False
        if res.order_line:
            for line in res.order_line:
                if line.commitment_date:
                    send_alert = True
        if send_alert:
            res._commitment_date_activity_create()
        res.rate = res.currency_id.rate
        return res

    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        send_alert = False
        if vals.get('order_line'):
            for line in vals['order_line']:
                for val in line:
                    if type(val) is dict:
                        if val.get('commitment_date'):
                            send_alert = True
        if send_alert:
            self._commitment_date_activity_create()
        return res

    def _commitment_date_activity_create(self):
        activity_type_id = self.env.ref(
            'mail.mail_activity_data_todo').sudo().id
        group_obj = self.env.ref(
            'monolitic_purchase.date_confirmation_alert_purchase_orders_group')
        for user in group_obj.users:
            # We need to search the summary in es_ES due to translation
            existing_activity = self.env['mail.activity'].search([
                ('summary', 'ilike', 'Pedido confirmado'),
                ('res_model_id', '=', self.env['ir.model']._get(self._name).id),
                ('res_id', '=', self.id),
                ('user_id', '=', user.id),
            ])
            if not existing_activity:
                activity_values = {
                    'activity_type_id': activity_type_id,
                    'user_id': user.id,
                    'summary': _("Order Confirmed."),
                    'date_deadline': (
                        datetime.today().date() + relativedelta(days=1)
                    ),
                    'res_model_id': self.env['ir.model']._get(self._name).id,
                    'res_id': self.id,
                }
                self.env['mail.activity'].create(activity_values)

    def _generate_inspection_activities(self):
        for po in self:
            for line in po.order_line:
                if line.product_id.incoming_inspection:
                    if not self.env.company.inspection_users:
                        raise UserError(_(
                            'A product from this Purchase Order needs '
                            'inspection but there are no inspection users set!'
                            '\n'
                            'Please check the Purchase Configuration '
                            'before proceeding.'))
                    inspectioners_list = \
                        self.env.company.inspection_users.mapped(
                            'partner_id').ids
                    activity_vals = {
                        'activity_type_id': self.env.ref(
                            'monolitic_purchase.mail_incoming_inspection').id,
                        'res_model_id': self.env['ir.model'].sudo()._get(
                            po._name).id,
                        'res_id': po.id,
                        'summary': 'Revisar pedido %s, referencia %s' % (
                            po.name, line.product_id.default_code),
                        'start_date': datetime.now(),
                        'assistants_ids': [(6, 0, inspectioners_list)],
                    }
                    self.env['mail.activity'].create(activity_vals)
        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    max_quantity = fields.Float(
        string='Maximum quantity',
        digits='Product Unit of Measure',
    )
    quantity_report = fields.Char(compute="_compute_quantity_report")
    requested_shipping_date = fields.Datetime(
        string='Requested Shipping Date',
        default=fields.Datetime.now(),
    )
    commitment_date = fields.Datetime(
        string='Commitment Date',
    )
    date_planned = fields.Datetime(string='Estimated Delivery Date')

    def create(self, values):
        res = super(PurchaseOrderLine, self).create(values)
        if res.product_id.categ_id.estimate_cost:
            res.estimated_perc = res.product_id.categ_id.estimate_cost
        return res

    @api.onchange('commitment_date', 'intrastat_transport_mode_id')
    def _onchange_commitment_date(self):
        if not self.product_id:
            return
        if self.commitment_date:
            self.date_planned = self.commitment_date + relativedelta(
                days=self.intrastat_transport_mode_id.transport_term
                if self.intrastat_transport_mode_id else 0
            )

    def _compute_quantity_report(self):
        for rec in self:
            rec.quantity_report = str(int(
                rec.product_qty)) + ' - ' + str(int(rec.max_quantity))

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        for rec in self:
            suppliers = rec.product_id.seller_ids.search([('name', '=', rec.order_id.partner_id.id)])
            for s in suppliers:
                if s.min_qty <= self.product_qty and s.max_quantity >= self.product_qty:
                    rec.max_quantity = s.max_quantity

        return res
