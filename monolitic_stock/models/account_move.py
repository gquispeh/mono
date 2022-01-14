# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('invoice_line_ids')
    def _onchange_product(self):
        for line in self.invoice_line_ids:
            if (
                line.product_id.id == self.env.ref(
                    'l10n_es_dua.producto_dua_valoracion_10').id or
                line.product_id.id == self.env.ref(
                    'l10n_es_dua.producto_dua_valoracion_21').id or
                line.product_id.id == self.env.ref(
                    'l10n_es_dua.producto_dua_valoracion_4').id
            ):
                self.fiscal_position_id = self.env.ref('l10n_es_dua.1_fp_dua')
