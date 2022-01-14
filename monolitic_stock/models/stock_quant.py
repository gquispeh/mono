from odoo import api, fields, models
from psycopg2 import OperationalError
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    quant_sequence_ids = fields.One2many(comodel_name='stock.quant.sequence',
                                         inverse_name='quant_id',
                                         string='Sequence')

    # Override to avoid this constraint
    @api.constrains('quantity')
    def check_quantity(self):
        for quant in self:
            if 1 != 1:
                raise ValidationError(_('The serial number has already been assigned: \n Product: %s, Serial Number: %s') % (quant.product_id.display_name, quant.lot_id.name))

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None, **args):
        """ Increase or decrease `reserved_quantity` of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.
        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
        if lot_id and quantity > 0:
            quants = quants.filtered(lambda q: q.lot_id)

        incoming_dates = [d for d in quants.mapped('in_date') if d]
        incoming_dates = [fields.Datetime.from_string(incoming_date) for incoming_date in incoming_dates]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = fields.Datetime.to_string(min(incoming_dates))
        else:
            in_date = fields.Datetime.now()

        for quant in quants:
            try:
                with self._cr.savepoint():
                    self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id], log_exceptions=False)
                    quant.write({
                        'quantity': quant.quantity + quantity,
                        'in_date': in_date,
                    })
                    if quantity > 0:
                        self.env['stock.quant.sequence'].create({
                            'quant_id': quant.id,
                            'quantity': quantity
                        })
                    break
            except OperationalError as e:
                if e.pgcode == '55P03':  # could not obtain the lock
                    continue
                else:
                    # Because savepoint doesn't flush, we need to invalidate the cache
                    # when there is a error raise from the write (other than lock-error)
                    self.clear_caches()
                    raise
        else:
            quant = self.create({
                'product_id': product_id.id,
                'location_id': location_id.id,
                'quantity': quantity,
                'lot_id': lot_id and lot_id.id,
                'package_id': package_id and package_id.id,
                'owner_id': owner_id and owner_id.id,
                'in_date': in_date,
            })
            if quantity > 0:
                self.env['stock.quant.sequence'].create({
                    'quant_id': quant.id,
                    'quantity': quantity
                })
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=False, allow_negative=True), fields.Datetime.from_string(in_date)
