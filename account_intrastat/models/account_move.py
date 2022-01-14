# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.sql import column_exists, create_column


class AccountMove(models.Model):
    _inherit = 'account.move'

    intrastat_transport_mode_id = fields.Many2one('account.intrastat.code', string='Intrastat Transport Mode',
                                                  readonly=True,
                                                  states={'draft': [('readonly', False)]}, domain="[('type', '=', 'transport')]")
    intrastat_airport_id = fields.Many2one('account.intrastat.code', string='Intrastat Port / Airport',
                                           readonly=True, states={'draft': [('readonly', False)]},
                                           domain="[('type', '=', 'airport')]")
    intrastat_country_id = fields.Many2one('res.country', string='Intrastat Country',
                                           help='Intrastat country, arrival for sales, dispatch for purchases',
                                           readonly=True, states={'draft': [('readonly', False)]}, domain=[('intrastat', '=', True)])
    intrastat_country_origin_id = fields.Many2one('res.country', string='Intrastat Origin Country',
                                                  help='Intrastat origin country, dispatch for sales, arrival for purchases',
                                                  readonly=True, states={'draft': [('readonly', False)]},
                                                  domain=[('intrastat', '=', True)])

    def _get_invoice_intrastat_country_id(self):
        ''' Hook allowing to retrieve the intrastat country depending of installed modules.
        :return: A res.country record's id.
        '''
        self.ensure_one()
        return self.partner_id.country_id.id

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id.country_id.intrastat:
            country = self._get_invoice_intrastat_country_id()
            self.intrastat_country_id = country
            self.intrastat_country_origin_id = country
        else:
            self.intrastat_country_id = False

        if self.partner_id.incoterm_id:
            self.incoterm_id = self.partner_id.incoterm_id

        if self.partner_id.intrastat_transport_mode_id:
            self.intrastat_transport_mode_id = \
                self.partner_id.intrastat_transport_mode_id

        if self.partner_id.intrastat_airport_id:
            self.intrastat_airport_id = self.partner_id.intrastat_airport_id

        return res

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        """
        Correctly set intrastat_country_id
        @override
        """
        values = super(AccountMove, self)._prepare_refund(
            invoice, date_invoice, date, description, journal_id)
        if 'intrastat_country_id' not in values:
            values['intrastat_country_id'] = invoice.intrastat_country_id.id
        if 'intrastat_country_origin_id' not in values:
            values['intrastat_country_origin_id'] = invoice.intrastat_country_origin_id.id
        if 'incoterm_id' not in values:
            values['incoterm_id'] = invoice.incoterm_id.id
        if 'intrastat_transport_mode_id' not in values:
            values['intrastat_transport_mode_id'] = invoice.intrastat_transport_mode_id.id
        if 'intrastat_airport_id' not in values:
            values['intrastat_airport_id'] = invoice.intrastat_airport_id.id
        return values

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _auto_init(self):
        if not column_exists(self.env.cr, "account_move_line", "intrastat_product_origin_country_id"):
            create_column(self.env.cr, "account_move_line", "intrastat_product_origin_country_id", "int4")
        return super()._auto_init()

    intrastat_transaction_id = fields.Many2one('account.intrastat.code', string='Intrastat', domain="[('type', '=', 'transaction')]")
    intrastat_transport_mode_id = fields.Many2one('account.intrastat.code', string='Intrastat Transport Mode',
                                                    domain="[('type', '=', 'transport')]")
    intrastat_product_origin_country_id = fields.Many2one('res.country', string='Product Country', compute='_compute_origin_country', store=True, readonly=False)

    @api.depends('product_id')
    def _compute_origin_country(self):
        for line in self:
            line.intrastat_product_origin_country_id = line.product_id.product_tmpl_id.intrastat_origin_country_id
