from odoo import models, api, _

class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        hide = [
            'price'
        ]
        res = super(ProductSupplierinfo, self).fields_get(allfields, attributes=attributes)
        for field in hide:
            if field in res:
                res[field]['searchable'] = False
                res[field]['sortable'] = False
                res[field]['exportable'] = False
        return res
