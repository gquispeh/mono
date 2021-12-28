from odoo import _, api, fields, models
import datetime

from datetime import datetime, timedelta, time

class SaleTickets(models.Model):
    _name = 'sale.tickets'

    name = fields.Char(string='Tickets')
    order_id = fields.Many2one('sale.order', string='Oferta')
    partner_id = fields.Many2one('res.partner',string='Cliente',required=True)

    solicitud = fields.Char(string='Solicitud')
    precio = fields.Float(string='Precio',digits=(12,2))
    plazo = fields.Char(string='Plazo')
    asunto = fields.Char(string='Asunto', required=True)
    autor_id = fields.Many2one('res.users', string='Autor', required=True)
    asignado_id = fields.Many2one('res.users', string='Asignado a', required=True)

    products_ids = fields.Many2many('product.product', string='Productos',readonly=False,compute="compute_product_ids",store=True)
    currency_id = fields.Many2one('res.currency', string='Tarifa de venta', required=True)
    fecha_entrega = fields.Date(string='Plazo de entrega solicitado')
    proveedor_ids = fields.Many2many('res.partner', string='Proveedores')
    state = fields.Selection([
        ('0', 'Nuevo'),
        ('1', 'Solicitud enviada'),
        ('2', 'En proceso'),
        ('3', 'Informada'),
        ('4', 'Cancelada')
    ], string='Estado', default='0')

    line_ids = fields.Many2many('sale.order.line',string='Lineas de Oferta',compute="compute_line_ids",store=True)
    descripcion = fields.Text(string='Descripción')
    porcertage = fields.Integer(string='Porcentaje de éxito')
    monetary_expected = fields.Float(string='Previsión de oportunidad', digits=(14, 2))

    @api.depends('order_id')
    def compute_line_ids(self):
        for rec in self:
            if rec.order_id:
                rec.line_ids = rec.order_id.order_line

    @api.depends('order_id')
    def compute_product_ids(self):
        for rec in self:
            if rec.order_id:
                rec.products_ids = rec.order_id.order_line.product_id


    def set_state_to_solitud(self):
        
        now = fields.datetime.now()
        if self.state == '0':
            activity_id = self.env['mail.activity'].create({
                'summary': 'Tienes una solicitud de precio y plazo pendiente',
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'sale.order')], limit=1).id,
                'res_id': self.order_id.id,
                'user_id': self.asignado_id.id,
                'date_deadline': (now + timedelta(days=2)).date()
        })
        self.write({'state': '1'})
        pass

    def set_state_to_proceso(self):
        now = fields.datetime.now()
        if self.state == '1':
            message = self.env['mail.message'].create({
							'subject': 'State',
							'body': 'Se ha solicitado precio y plazo al proveedor',
							'author_id': self.env.user.partner_id.id,
							'model': 'sale.order',
							'res_id': self.order_id.id,
						})
            self.write({'state': '2'})
            pass

    def set_state_to_informada(self):
        now = fields.datetime.now()
        if self.state == '2':
            message = self.env['mail.message'].create({
							'subject': 'State',
							'body': 'Se informado del precio y plazo de entrega',
							'author_id': self.env.user.partner_id.id,
							'model': 'sale.order',
							'res_id': self.order_id.id,
						})
            self.write({'state': '3'})
            pass

    def set_state_to_cancel(self):
        message = self.env['mail.message'].create({
                        'subject': 'State',
                        'body': 'Se ha cancelado la solicitud de precio y plazo',
                        'author_id': self.env.user.partner_id.id,
                        'model': 'sale.order',
                        'res_id': self.order_id.id,
                    })
        self.write({'state': '4'})
        pass

class SaleOrderTickets(models.Model):
    _inherit = 'sale.order'

    tickets_count = fields.Integer(compute='compute_count_tickets')

    def compute_count_tickets(self):
        for record in self:
            count = self.env['sale.tickets'].search_count([('order_id', '=', self.id)])
            if count:
                record.tickets_count = count
            else:
                record.tickets_count = 0

    def get_tickets(self):
        self.ensure_one()
        user = self.env['res.users'].sudo().browse(self.env.uid)
        return {"type":"ir.actions.act_window",
                "view_mode": 'tree,form',
                "view_type": 'form',
                "res_model":"sale.tickets",
                'target': 'current',
                "context":{"default_order_id":self.id,
                        "default_autor_id":user.id,
                        "default_asignado_id":self.user_id.id,
                        "default_name":'Ticket {}'.format(self.name),
                        "default_currency_id":self.currency_id.id,
                        "default_partner_id":self.partner_id.id}}
