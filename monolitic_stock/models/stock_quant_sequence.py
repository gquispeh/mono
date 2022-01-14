from odoo import api, fields, models


class StockQuantSequence(models.Model):
    _name = 'stock.quant.sequence'
    _description = 'Sequence on Quants for FIFO'
    _rec_name = 'fifo_name'
    _order = 'sequence ASC'

    _sql_constraints = [
        (
            'valid_quant_qty',
            'CHECK (quantity >= 0)',
            'Quantity can''t be negative !'),
        (
            'valid_reserved_qty',
            'CHECK(reserved_qty >= 0)',
            'Reserved quantity can''t be negative !'
        )
    ]

    fifo_name = fields.Char(
        'FIFO Name',
        compute='_compute_fifo_name',
        store=True,
    )
    sequence = fields.Integer(
        readonly=True,
        required=True,
    )
    quantity = fields.Integer()
    quant_id = fields.Many2one(comodel_name='stock.quant')

    @api.depends('sequence')
    def _compute_fifo_name(self):
        for seq in self:
            seq.fifo_name = 'F' + str(seq.sequence)

    @api.model
    def create(self, values):
        sequence = 0
        if 'quant_id' in values:
            sequence_obj = self.env['stock.quant.sequence'].search([
                ('quant_id', '=', values['quant_id'])
            ])
            if sequence_obj:
                sequence += sequence_obj[-1].sequence + 1

        values.update({'sequence': sequence})
        result = super(StockQuantSequence, self).create(values)
        return result
