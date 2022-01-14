# Copyright 2020 Sergi Oliva <sergi.oliva@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

import logging
_logger = logging.getLogger(__name__)


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    url = fields.Char(
        string="Wiki URL"
    )

    def get_menu_id(self, url=False):
        for rec in self:
            if url:
                if url == '/web' or 'home' in url:
                    return 'https://wiki.monolitic.com/tic/erp/primeros-pasos-en-odoo/'

                elif 'action' and 'menu_id' in url:
                    action_id = url.split('action=')[-1].split('&')[0]
                    menu_id = url.split('menu_id=')[-1]

                    #  Query to search the current menu with the action
                    # because on the URL we only have the last parent menu id
                    query = """
                        SELECT id
                        FROM ir_ui_menu
                        WHERE action LIKE %s
                        AND parent_path LIKE %s
                        ORDER BY id
                    """
                    self.env.cr.execute(query, (
                        '%' + ',' + action_id + '%',
                        '%' + menu_id + '%'
                    ))
                    res = self.env.cr.dictfetchall()

                    # Get menu if found, else get main menu
                    if res:
                        res_menu_id = res[-1]['id']
                        menu_obj = self.env[
                            'ir.ui.menu'].sudo().browse(int(res_menu_id))
                    else:
                        menu_obj = self.env[
                            'ir.ui.menu'].sudo().browse(int(menu_id))

                    # Get URL from menu, else check every parent for its URL
                    if menu_obj.url:
                        return menu_obj.url
                    else:
                        url = ''
                        while menu_obj.parent_id:
                            if menu_obj.parent_id.url:
                                url = menu_obj.parent_id.url
                                break
                            menu_obj = menu_obj.parent_id

                        return url
            return False
